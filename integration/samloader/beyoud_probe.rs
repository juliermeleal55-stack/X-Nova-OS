// SPDX-License-Identifier: Apache-2.0
// Metadata-only probe using the pinned samloader-rs API. No IMEI and no download.
use samloader_fus::FusClient;

fn valid_firmware_version(value: &str) -> bool {
    let parts: Vec<&str> = value.split('/').collect();
    parts.len() == 4
        && parts.iter().all(|part| {
            !part.is_empty() && part.bytes().all(|byte| byte.is_ascii_alphanumeric())
        })
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    assert!(
        args.len() == 3 || args.len() == 4,
        "usage: beyoud_probe MODEL CSC [EXACT_FOUR_PART_VERSION]"
    );

    let exact_version = if args.len() == 4 {
        let version = args[3].as_str();
        assert!(
            valid_firmware_version(version),
            "Expected a four-part exact firmware version"
        );
        Some(version.to_owned())
    } else {
        None
    };

    let mut client = FusClient::new().expect("SmartDownload handshake failed");
    let version = match exact_version.as_ref() {
        Some(version) => version.clone(),
        None => {
            let history = client
                .fetch_history(&args[1], &args[2])
                .or_else(|_| samloader_fus::fetch_version_xml(&args[1], &args[2]))
                .expect("No firmware version available for configured model/CSC");
            assert!(!history.latest.is_empty(), "Empty firmware version");
            history.latest
        }
    };

    println!(
        "Checking model={} CSC={} version={}",
        args[1], args[2], version
    );
    client.fetch_binary_info(&args[1], &args[2], &version);
    assert!(client.info.size > 0, "Empty firmware binary");
    assert!(!client.info.filename.is_empty(), "Firmware filename missing");
    if exact_version.is_some() {
        assert_eq!(
            client.info.version, version,
            "SmartDownload returned a different version than requested"
        );
    }
    println!(
        "BEYOUD_FIRMWARE\t{}\t{}\t{}\t{}",
        args[1], args[2], client.info.version, client.info.size
    );
    println!(
        "SmartDownload metadata accepted: version={} size={} bytes",
        client.info.version, client.info.size
    );
}
