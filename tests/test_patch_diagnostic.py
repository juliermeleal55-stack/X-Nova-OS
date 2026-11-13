import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from integration import build
from test_build_stages import fixture

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('diagnostic_summary',ROOT/'scripts/summarize_patch_diagnostic.py')
summary=importlib.util.module_from_spec(spec);spec.loader.exec_module(summary)


class PatchDiagnosticTests(unittest.TestCase):
    def test_diagnostic_runs_preflight_once_and_never_creates_patch_success_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root);calls=[]
            def command(cmd,workspace,env,telemetry):
                calls.append((cmd,env))
                (root/'out/beyoud-logs/patch-preflight.json').write_text(json.dumps({'status':'experimental-with-failures'}))
                return 100
            with patch.object(build,'environment',return_value={'BEYOUD_EXPERIMENTAL_ALLOW_PATCH_FAILURES':'1'}),patch.object(build,'validate_prior') as prior,patch.object(build,'inventory'),patch.object(build,'run_command',side_effect=command),patch.object(build,'normalize_static_layout') as normalize,contextlib.redirect_stdout(io.StringIO()):
                build.execute(root,'diagnostic')
                prior.assert_called_once()
                self.assertEqual(prior.call_args.args[1],'patch')
                normalize.assert_not_called()
            self.assertEqual(len(calls),1)
            self.assertEqual(calls[0][1]['BEYOUD_PATCH_PREFLIGHT'],'1')
            self.assertIn('--no-rom-zip',calls[0][0])
            self.assertFalse((root/'out/beyoud-stages/patch.json').exists())
            self.assertEqual(json.loads((root/'out/beyoud-stages/diagnostic.json').read_text())['status'],'diagnostic-complete')
            with self.assertRaises(ValueError):build.validate_prior(root,'retire',build.identity(root),'beyond2lte')

    def test_early_failure_summary_cannot_claim_patches_passed(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            result=summary.collect(Path(tmp))
            self.assertEqual(result['status'],'not-executed')
            self.assertEqual(result['prior_19_review']['counts'],{'passed':0,'failed':0,'not-executed':19})

    def test_partial_diagnostic_is_incomplete_not_clean(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp);logs=root/'out/beyoud-logs';logs.mkdir(parents=True)
            (logs/'patch-preflight.jsonl').write_text('{"kind":"start","status":"running"}\n{"truncated":')
            self.assertEqual(summary.collect(root)['status'],'incomplete')

    def test_workflow_gates_all_rom_producing_steps(self):
        text=(ROOT/'.github/workflows/alpha.yml').read_text()
        for name in ('Preflight modules and apply patches using pinned OneROM boot images',
                     'Capture package inputs and retire verified firmware trees',
                     'Build and verify the TWRP-installable ROM ZIP from RAW partition images',
                     'Validate TWRP ZIP; reject OTA payloads and recovery images',
                     'Upload only the TWRP-installable ROM ZIP'):
            self.assertIn('- name: '+name+'\n        if: ${{ !inputs.diagnostic_only }}',text)
        request=(ROOT/'.github/workflows/s24fe-patch-diagnostic-request.yml').read_text()
        self.assertIn('diagnostic_only: true',request)
        self.assertIn('experimental_patch_failures: true',request)
