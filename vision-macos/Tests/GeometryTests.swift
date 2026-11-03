import Foundation
import CoreGraphics

@main struct GeometryTests {
    static func near(_ a: CGFloat, _ b: CGFloat) -> Bool { abs(a-b) < 0.000001 }
    static func main() {
        let q = ScreenQuad(points: [CGPoint(x: 0.2, y: 0.9), CGPoint(x: 0.8, y: 0.8), CGPoint(x: 0.75, y: 0.1), CGPoint(x: 0.25, y: 0.2)])
        assert(q.isValid && q.contains(CGPoint(x: 0.5, y: 0.5)))
        assert(!q.contains(CGPoint(x: 0.05, y: 0.5)))
        assert(q.cornerTargets.allSatisfy { q.contains($0) })
        let crossed = ScreenQuad(points: [q.points[0], q.points[2], q.points[1], q.points[3]])
        assert(!crossed.isValid)
        let mapping = ImageMapping(image: CGSize(width: 1920, height: 1080), view: CGSize(width: 1000, height: 1000))
        assert(near(mapping.fitted.height, 562.5))
        let original = CGPoint(x: 0.23, y: 0.71)
        let recovered = mapping.imagePoint(mapping.display(original))!
        assert(near(original.x, recovered.x) && near(original.y, recovered.y))
        assert(mapping.imagePoint(CGPoint(x: 20, y: 20)) == nil)
        print("Geometry tests passed")
    }
}
