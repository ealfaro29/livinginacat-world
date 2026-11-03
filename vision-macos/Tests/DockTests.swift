import Foundation
import CoreGraphics
import CoreImage

@main struct DockTests {
    static func main() {
        let size = CGSize(width: 400, height: 850)
        let labels = [0.60, 0.43].flatMap { y in [0.14, 0.38, 0.62, 0.86].map { x in CGRect(x: x-0.04, y: y, width: 0.08, height: 0.012) } }
        let grid = Array(IconGrid.targets(for: labels, imageSize: size).values)
        let extent = CGRect(origin: .zero, size: size)
        let background = CIImage(color: CIColor(red: 0.06, green: 0.06, blue: 0.06)).cropped(to: extent)
        func iconImage(count: Int) -> CIImage {
            var image = background
            for x in [0.14, 0.38, 0.62, 0.86].prefix(count) {
                let rect = CGRect(x: x*400-34, y: 0.065*850-34, width: 68, height: 68)
                let color = CIImage(color: CIColor(red: 0.1, green: 0.7, blue: 0.25)).cropped(to: rect)
                let symbol = CIImage(color: CIColor(red: 1, green: 1, blue: 1)).cropped(to: rect.insetBy(dx: 20, dy: 20))
                image = symbol.composited(over: color.composited(over: image))
            }
            return image
        }
        let context = CIContext(options: [.useSoftwareRenderer: true])
        precondition(DockDetector.detect(in: background, grid: grid, context: context).isEmpty, "Blank dock must not invent icons")
        precondition(DockDetector.detect(in: iconImage(count: 1), grid: grid, context: context).isEmpty, "An isolated patch must not create a dock")
        precondition(DockDetector.detect(in: iconImage(count: 4), grid: [], context: context).isEmpty, "Dock requires a detected icon grid")
        let found = DockDetector.detect(in: iconImage(count: 4), grid: grid, context: context)
        precondition(found.count == 4, "Expected 4 dock icons; got \(found.count)")
        for (i, item) in found.enumerated() {
            precondition(item.slot == i+1 && abs(item.bounds.midY - 0.065) < 0.03, "Wrong dock position")
        }
        print("Dock icon detection tests passed")
    }
}
