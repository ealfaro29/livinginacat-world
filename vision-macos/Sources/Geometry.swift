import Foundation
import CoreGraphics

// Points are in camera-image coordinates, with (0, 0) at the bottom left.
struct ScreenQuad: Equatable {
    var points: [CGPoint] // top-left, top-right, bottom-right, bottom-left
    var isValid: Bool {
        guard points.count == 4, points.allSatisfy({ (0...1).contains($0.x) && (0...1).contains($0.y) }) else { return false }
        var signs: [CGFloat] = []
        for i in 0..<4 {
            let a = points[i], b = points[(i + 1) % 4], c = points[(i + 2) % 4]
            signs.append((b.x-a.x)*(c.y-b.y) - (b.y-a.y)*(c.x-b.x))
        }
        var twiceArea: CGFloat = 0
        for i in 0..<4 {
            let a = points[i], b = points[(i + 1) % 4]
            twiceArea += a.x * b.y - b.x * a.y
        }
        let area = abs(twiceArea) / 2
        return area > 0.01 && (signs.allSatisfy { $0 > 0.00001 } || signs.allSatisfy { $0 < -0.00001 })
    }
    func contains(_ p: CGPoint) -> Bool {
        guard isValid else { return false }
        var signs: [CGFloat] = []
        for i in 0..<4 {
            let a = points[i], b = points[(i + 1) % 4]
            signs.append((b.x-a.x)*(p.y-a.y) - (b.y-a.y)*(p.x-a.x))
        }
        return signs.allSatisfy { $0 >= -0.00001 } || signs.allSatisfy { $0 <= 0.00001 }
    }
    // Inset the targets so a visualized stylus is inside the rounded display.
    var cornerTargets: [CGPoint] {
        guard points.count == 4 else { return [] }
        let center = CGPoint(x: points.map(\.x).reduce(0,+)/4, y: points.map(\.y).reduce(0,+)/4)
        return points.map { CGPoint(x: $0.x * 0.94 + center.x * 0.06, y: $0.y * 0.94 + center.y * 0.06) }
    }
}

struct ImageMapping {
    let image: CGSize
    let view: CGSize
    var fitted: CGRect {
        guard image.width > 0, image.height > 0, view.width > 0, view.height > 0 else { return .zero }
        let scale = min(view.width / image.width, view.height / image.height)
        let size = CGSize(width: image.width * scale, height: image.height * scale)
        return CGRect(x: (view.width-size.width)/2, y: (view.height-size.height)/2, width: size.width, height: size.height)
    }
    func display(_ point: CGPoint) -> CGPoint {
        let r = fitted
        return CGPoint(x: r.minX + point.x * r.width, y: r.minY + (1-point.y) * r.height)
    }
    func imagePoint(_ point: CGPoint) -> CGPoint? {
        let r = fitted
        guard r.width > 0, r.height > 0, r.contains(point) else { return nil }
        return CGPoint(x: (point.x-r.minX)/r.width, y: 1-(point.y-r.minY)/r.height)
    }
}
