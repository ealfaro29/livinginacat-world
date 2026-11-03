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

// Home-screen icons sit above labels in repeated, evenly spaced rows. Infer a
// conservative target only when at least two rows share three or more columns.
// OCR alone cannot tell whether arbitrary text is an interactive element.
struct IconGrid {
    static func targets(for labels: [CGRect], imageSize: CGSize) -> [Int: CGRect] {
        guard imageSize.width > 0, imageSize.height > 0 else { return [:] }
        struct Row { var indices: [Int]; var y: CGFloat }
        var rows: [Row] = []
        for i in labels.indices.sorted(by: { labels[$0].midY > labels[$1].midY }) {
            let rect = labels[i]
            guard rect.width > 0, rect.height > 0, rect.width < 0.32, rect.height < 0.045 else { continue }
            let tolerance = min(0.018, max(0.008, rect.height * 0.85))
            if let j = rows.indices.first(where: { abs(rows[$0].y - rect.midY) <= tolerance }) {
                rows[j].indices.append(i)
                rows[j].y = rows[j].indices.map { labels[$0].midY }.reduce(0, +) / CGFloat(rows[j].indices.count)
            } else { rows.append(Row(indices: [i], y: rect.midY)) }
        }
        let eligible = rows.filter { $0.indices.count >= 3 }
        var accepted: Set<Int> = []
        var spacings: [CGFloat] = []
        for i in eligible.indices {
            let left = eligible[i].indices.sorted { labels[$0].midX < labels[$1].midX }
            for j in eligible.indices where j > i {
                let right = eligible[j].indices.sorted { labels[$0].midX < labels[$1].midX }
                let matches = left.filter { a in right.contains { abs(labels[a].midX - labels[$0].midX) < 0.045 } }
                guard matches.count >= 3 else { continue }
                let gaps = zip(matches, matches.dropFirst()).map { labels[$1].midX - labels[$0].midX }.filter { (0.13...0.34).contains($0) }
                guard gaps.count >= 2, let low = gaps.min(), let high = gaps.max(), high / low < 1.4 else { continue }
                accepted.formUnion(left); accepted.formUnion(right); spacings.append(contentsOf: gaps)
            }
        }
        guard !spacings.isEmpty else { return [:] }
        spacings.sort()
        let width = spacings[spacings.count / 2] * 0.72
        let height = width * imageSize.width / imageSize.height
        guard height > 0.025, height < 0.18 else { return [:] }
        var result: [Int: CGRect] = [:]
        for index in accepted {
            let label = labels[index]
            let rect = CGRect(x: label.midX - width / 2, y: label.maxY + height * 0.08, width: width, height: height)
            guard rect.minX >= 0, rect.maxX <= 1, rect.maxY <= 1 else { continue }
            result[index] = rect
        }
        return result
    }
}
