// Logitech C922 UVC extension unit. Only the documented LED mode byte is changed.
#import <Foundation/Foundation.h>
#import "UVCController.h"
#include <string.h>

@interface UVCController (CatLED)
- (BOOL)getData:(void *)value ofType:(int)type withLength:(int)length fromSelector:(int)selector atUnitId:(int)unit;
- (BOOL)setData:(void *)value withLength:(int)length forSelector:(int)selector atUnitId:(int)unit;
- (int)catLEDUnit;
@end

@implementation UVCController (CatLED)
- (int)catLEDUnit {
    const unsigned char guid[16] = {0x21,0x2d,0xe5,0xff,0x30,0x80,0x2c,0x4e,0x82,0xd9,0xf5,0x87,0xd0,0x05,0x40,0xbd};
    IOUSBDescriptorHeader *header = (*_controllerInterface)->FindNextAssociatedDescriptor(_controllerInterface, NULL, 0x24);
    if (!header) return -1;
    const unsigned char *p = (const unsigned char *)header;
    if (p[0] < 7 || p[2] != 1) return -1;
    int total = p[5] | p[6] << 8;
    if (total < 7 || total > 4096) return -1;
    for (int i = 0; i + 3 <= total;) {
        int n = p[i];
        if (n < 3 || i + n > total) break;
        if (n >= 20 && p[i+2] == 6 && memcmp(p+i+4, guid, 16) == 0) return p[i+3];
        i += n;
    }
    return -1;
}
@end

int main(int argc, const char **argv) {
    @autoreleasepool {
        if (argc != 3) return 2;
        NSString *name = [NSString stringWithUTF8String:argv[1]];
        char *end = NULL; long mode = strtol(argv[2], &end, 10);
        if (!*argv[2] || *end || mode < 0 || mode > 3) return 2;
        UVCController *selected = nil; int count = 0;
        for (UVCController *c in [UVCController uvcControllers]) {
            if ([c vendorId] == 0x046d && [c productId] == 0x085c && [[c deviceName] isEqualToString:name]) { selected = c; count++; }
        }
        if (count != 1) return 3;
        int unit = [selected catLEDUnit];
        unsigned char info = 0, len[2] = {0}, data[5] = {0};
        if (unit < 0 || ![selected getData:&info ofType:0x86 withLength:1 fromSelector:9 atUnitId:unit] || (info & 3) != 3 ||
            ![selected getData:len ofType:0x85 withLength:2 fromSelector:9 atUnitId:unit] || (len[0] | len[1]<<8) != 5 ||
            ![selected getData:data ofType:0x81 withLength:5 fromSelector:9 atUnitId:unit] || data[1] > 3) return 4;
        int previous = data[1]; data[1] = (unsigned char)mode;
        if (![selected setData:data withLength:5 forSelector:9 atUnitId:unit]) return 5;
        unsigned char verify[5] = {0};
        if (![selected getData:verify ofType:0x81 withLength:5 fromSelector:9 atUnitId:unit] || verify[1] != mode) {
            data[1] = (unsigned char)previous;
            [selected setData:data withLength:5 forSelector:9 atUnitId:unit];
            return 6;
        }
        printf("%d\n", previous);
        return 0;
    }
}
