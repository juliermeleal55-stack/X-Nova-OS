import json
import os
import zipfile
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from integration.framework_policy import install, APKTOOL

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / 'integration/artisan/apktool.sh'


class ApktoolOverlayTests(unittest.TestCase):
    def test_workspace_accepts_upstream_then_installs_overlay_not_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            shutil.copytree(ROOT / 'reference/build', workspace, dirs_exist_ok=True)
            original = (workspace / APKTOOL).read_bytes()
            self.assertNotEqual(original, OVERLAY.read_bytes())
            install(workspace)
            self.assertEqual((workspace / APKTOOL).read_bytes(), OVERLAY.read_bytes())
            self.assertEqual((ROOT / 'reference/build' / APKTOOL).read_bytes(), original)
            subprocess.run(['bash', '-n', str(workspace / APKTOOL)], check=True)

    def test_unknown_upstream_still_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            shutil.copytree(ROOT / 'reference/build', workspace, dirs_exist_ok=True)
            (workspace / APKTOOL).write_text('unexpected source')
            with self.assertRaises(ValueError):
                install(workspace)

    def test_decode_executes_correct_per_dex_mapping_and_single_pass(self):
        text = OVERLAY.read_text()
        worker = text[text.index('WAIT_FOR_DEX_WORKERS()\n'):text.index('BUILD()\n')]
        decode = worker + text[text.index('DECODE()\n'):text.index('DEX_TO_API()\n')]
        for name, expected in [('other.jar', {'smali': '35', 'smali_classes2': '34'}),
                               ('services.jar', {'smali': '35', 'smali_classes2': '34'}),
                               ('container.jar', {'smali': '35', 'smali_classes2': '35', 'smali_classes3': '34'})]:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = root / name
                with zipfile.ZipFile(source,'w') as archive:
                    archive.writestr('classes.dex',b'fixture-primary')
                    archive.writestr('classes2.dex',b'fixture-secondary')
                tools=root/'bin';tools.mkdir()
                tool=tools/'baksmali'
                tool.write_text("""#!/usr/bin/env python3
import sys
source=sys.argv[-1]
container='container.jar' in source
if sys.argv[1:3]==['list','dex']:
 print('classes.dex\\nclasses.dex/2\\nclasses2.dex' if container else 'classes.dex\\nclasses2.dex')
elif sys.argv[1:3]==['list','classes']:
 n=1 if source.endswith('/classes.dex') else (3 if container and source.endswith('/classes2.dex') else 2)
 print('Lp/Probe'+str(n)+';')
else:sys.exit(2)
""")
                tool.chmod(0o755)
                env=dict(os.environ,PATH=str(tools)+os.pathsep+os.environ['PATH'])
                output = root / 'decoded'
                harness = r'''
LOG() { :; }; LOGE() { echo "$*" >&2; }; READ_BYTES_AT() { echo 04034b50; }
EVAL() { eval "$1"; }
apktool() { mkdir -p "$OUTPUT_PATH"; touch "$OUTPUT_PATH/classes.dex" "$OUTPUT_PATH/classes2.dex"; }
DEX_TO_API() { if [[ "$1" == */classes.dex ]]; then echo 35; else echo 34; fi; }
baksmali() {
 local output="" api=""
 while [ "$#" -gt 0 ]; do
  case "$1" in -o) output="$2"; shift 2 ;; -a) api="$2"; shift 2 ;; *) shift ;; esac
 done
 mkdir "$OUTPUT_PATH/inflight" || return 1
 sleep 0.02
 mkdir -p "$output"
 echo "$api" >> "$output/invocations"
 local n=1
 [[ "$output" == */smali_classes2 ]] && n=2
 [[ "$output" == */smali_classes3 ]] && n=3
 mkdir -p "$output/p"
 printf '.class public Lp/Probe%s;\n.super Ljava/lang/Object;\n' "$n" > "$output/p/Probe$n.smali"
 rmdir "$OUTPUT_PATH/inflight"
}
'''
                script = root / 'test.sh'
                (root/'integration').mkdir()
                shutil.copyfile(ROOT/'integration/dex_entries.py',root/'integration/dex_entries.py')
                harness='SRC_DIR='+str(root)+'\n'+harness
                script.write_text(harness + decode + '\nINPUT_FILE="$1"; OUTPUT_PATH="$2"; FORCE=false; THREAD_COUNT=1; DECODE\n')
                result = subprocess.run(['bash', str(script), str(source), str(output)], text=True, capture_output=True,env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                records=list((root/'out/beyoud-logs/dex-inventory').glob('*.json'))
                self.assertEqual(len(records),1)
                evidence=json.loads(records[0].read_text())
                self.assertEqual(evidence['unique_classes'],len(expected))
                self.assertEqual(len(evidence['units']),len(expected))
                self.assertTrue((output/'.beyoud_decode_complete').is_file())
                rows = (output / 'dex_api_versions.tsv').read_text().splitlines()
                self.assertEqual(len(rows), len(expected))
                self.assertEqual(dict(line.split('\t') for line in rows), expected)
                for folder, api in expected.items():
                    self.assertEqual((output / folder / 'invocations').read_text().splitlines(), [api])
                # Execute the real assembly loop against the metadata just emitted.
                build = worker + text[text.index('BUILD()\n'):text.index('    # Copy original META-INF')] + '}\n'
                mock = r'''
smali() {
 local output="" api=""
 while [ "$#" -gt 0 ]; do
  case "$1" in -o) output="$2"; shift 2 ;; -a) api="$2"; shift 2 ;; *) shift ;; esac
 done
 printf '%s' "$api" > "$output"
}
'''
                script.write_text(harness + mock + build + '\nINPUT_FILE="$1"; OUTPUT_PATH="$2"; THREAD_COUNT=1; BUILD\n')
                assembled = subprocess.run(['bash', str(script), str(source), str(output)], text=True, capture_output=True)
                self.assertEqual(assembled.returncode, 0, assembled.stderr)
                self.assertEqual((output / 'classes.dex').read_text(), expected['smali'])
                self.assertEqual((output / 'classes2.dex').read_text(), expected['smali_classes2'])
                if 'smali_classes3' in expected:
                    self.assertEqual((output/'classes3.dex').read_text(),expected['smali_classes3'])


    def test_failed_earlier_dex_worker_cannot_be_hidden_by_last_success(self):
        text = OVERLAY.read_text()
        worker = text[text.index('WAIT_FOR_DEX_WORKERS()\n'):text.index('BUILD()\n')]
        script = worker + '\nBEYOUD_DEX_PIDS=(); (exit 7) & BEYOUD_DEX_PIDS+=("$!"); (exit 0) & BEYOUD_DEX_PIDS+=("$!"); WAIT_FOR_DEX_WORKERS\n'
        self.assertNotEqual(subprocess.run(['bash','-c',script]).returncode,0)

    def test_services_api_override_cannot_reintroduce_unsupported_api_36(self):
        text=OVERLAY.read_text()
        self.assertNotIn('&& DEX_API_LEVEL=36',text)
        worker=text[text.index('WAIT_FOR_DEX_WORKERS()\n'):text.index('BUILD()\n')]
        build=worker+text[text.index('BUILD()\n'):text.index('    # Copy original META-INF')]+'}\n'
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);(output/'smali').mkdir()
            (output/'dex_api_versions.tsv').write_text('smali\t36\n')
            harness='LOG() { :; }; LOGE() { echo "$*" >&2; }; smali() { echo SHOULD_NOT_ASSEMBLE; };\n'
            result=subprocess.run(['bash','-c',harness+build+'\nOUTPUT_PATH="$1"; INPUT_FILE=services.jar; THREAD_COUNT=1; BUILD','test',str(output)],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Invalid DEX API level',result.stderr)
            self.assertNotIn('SHOULD_NOT_ASSEMBLE',result.stdout)

    def test_dex_header_mapping_reads_full_magic_not_last_ascii_digit(self):
        text=OVERLAY.read_text()
        mapper=text[text.index('DEX_TO_API()\n'):text.index('PREPARE_SCRIPT()\n')]
        original=(ROOT/'reference/build/scripts/utils/build_utils.sh').read_text()
        reader=original[original.index('READ_BYTES_AT()\n'):original.index('\n# [',original.index('READ_BYTES_AT()\n'))]
        harness='LOGE() { echo "$*" >&2; }; _CHECK_NON_EMPTY_PARAM() { [[ -n "$2" ]]; };\n'+reader+'\n'
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'classes.dex'
            for version,api in [('035','23'),('037','25'),('038','27'),('039','29'),('040','34'),('041','35')]:
                path.write_bytes(('dex\n'+version+'\0').encode())
                result=subprocess.run(['bash','-c',harness+mapper+'\nDEX_TO_API "$1"','test',str(path)],capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(result.stdout.strip(),api)
            path.write_bytes(b'dex\n999\0')
            result=subprocess.run(['bash','-c',harness+mapper+'\nDEX_TO_API "$1"','test',str(path)],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
