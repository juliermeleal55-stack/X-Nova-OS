typedef struct {
    __SIZE_TYPE__ storage[3];
} LegacyString;

#if __SIZEOF_POINTER__ == 8
extern void string_init(LegacyString *, const char *, __SIZE_TYPE__)
    __asm__("_ZNSt3__112basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEE6__initEPKcm");
extern void configure_rpc(__SIZE_TYPE__, unsigned char)
    __asm__("_ZN7android8hardware22configureRpcThreadpoolEmb");
#else
extern void string_init(LegacyString *, const char *, __SIZE_TYPE__)
    __asm__("_ZNSt3__112basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEE6__initEPKcj");
extern void configure_rpc(__SIZE_TYPE__, unsigned char)
    __asm__("_ZN7android8hardware22configureRpcThreadpoolEjb");
#endif
extern void string_destroy(LegacyString *)
    __asm__("_ZNSt3__112basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEED1Ev");
extern int register_service(const LegacyString *, const LegacyString *, const LegacyString *)
    __asm__("_ZN7android8hardware40registerPassthroughServiceImplementationERKNSt3__112basic_stringIcNS1_11char_traitsIcEENS1_9allocatorIcEEEES9_S9_");
extern void join_rpc(void)
    __asm__("_ZN7android8hardware17joinRpcThreadpoolEv");
extern int __android_log_print(int, const char *, const char *, ...);

int main(void)
{
#ifdef S10_BLUETOOTH_AUDIO
    static const char descriptor[] = "vendor.samsung.hardware.bluetooth.audio@2.1::ISehBluetoothAudioProvidersFactory";
#else
    static const char descriptor[] = "android.hardware.soundtrigger@2.0::ISoundTriggerHw";
#endif
    LegacyString interface_name = {{0, 0, 0}};
    LegacyString instance_name = {{0, 0, 0}};
    int status;

    string_init(&interface_name, descriptor, sizeof(descriptor) - 1);
    string_init(&instance_name, "default", 7);
    configure_rpc(4, 1);
    status = register_service(&interface_name, &interface_name, &instance_name);
#ifdef S10_BLUETOOTH_AUDIO
    __android_log_print(4, "S10BluetoothAudio", "Bluetooth audio registration status: %d", status);
#else
    __android_log_print(4, "S10SoundTrigger", "SoundTrigger registration status: %d", status);
#endif
    string_destroy(&instance_name);
    string_destroy(&interface_name);
    if (status != 0) {
        return 1;
    }
    join_rpc();
    return 0;
}