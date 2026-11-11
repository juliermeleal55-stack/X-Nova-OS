// Android 17 libui symbols missing from the Android 16 gralloc2-capable libui.
// Build: clang --target=aarch64-linux-android31 -nostdlib -shared -fuse-ld=lld \
//          -Wl,-soname,libui_shim.so -o libui_shim.so libui_shim.S

    .text

// status_t GraphicBufferMapper::getSmpte2094_50(const native_handle_t*, std::optional<std::vector<uint8_t>>*)
    .globl _ZN7android19GraphicBufferMapper15getSmpte2094_50EPK13native_handlePNSt3__18optionalINS4_6vectorIhNS4_9allocatorIhEEEEEE
    .type  _ZN7android19GraphicBufferMapper15getSmpte2094_50EPK13native_handlePNSt3__18optionalINS4_6vectorIhNS4_9allocatorIhEEEEEE, %function
// status_t GraphicBufferMapper::setSmpte2094_50(const native_handle_t*, std::optional<std::vector<uint8_t>>)
    .globl _ZN7android19GraphicBufferMapper15setSmpte2094_50EPK13native_handleNSt3__18optionalINS4_6vectorIhNS4_9allocatorIhEEEEEE
    .type  _ZN7android19GraphicBufferMapper15setSmpte2094_50EPK13native_handleNSt3__18optionalINS4_6vectorIhNS4_9allocatorIhEEEEEE, %function
// status_t GraphicBuffer::getSmpte2094_50(std::optional<std::vector<uint8_t>>*) const
    .globl _ZNK7android13GraphicBuffer15getSmpte2094_50EPNSt3__18optionalINS1_6vectorIhNS1_9allocatorIhEEEEEE
    .type  _ZNK7android13GraphicBuffer15getSmpte2094_50EPNSt3__18optionalINS1_6vectorIhNS1_9allocatorIhEEEEEE, %function
_ZN7android19GraphicBufferMapper15getSmpte2094_50EPK13native_handlePNSt3__18optionalINS4_6vectorIhNS4_9allocatorIhEEEEEE:
_ZN7android19GraphicBufferMapper15setSmpte2094_50EPK13native_handleNSt3__18optionalINS4_6vectorIhNS4_9allocatorIhEEEEEE:
_ZNK7android13GraphicBuffer15getSmpte2094_50EPNSt3__18optionalINS1_6vectorIhNS1_9allocatorIhEEEEEE:
    hint #34                    // bti c
    mov  w0, #-38               // INVALID_OPERATION, same as gralloc2's unsupported-metadata result
    ret

// std::string decodeGrallocUsage(uint64_t): returns an empty libc++ short string via x8
    .globl _Z18decodeGrallocUsagem
    .type  _Z18decodeGrallocUsagem, %function
_Z18decodeGrallocUsagem:
    hint #34                    // bti c
    stp  xzr, xzr, [x8]
    str  xzr, [x8, #16]
    ret

    .section .note.GNU-stack,"",%progbits
