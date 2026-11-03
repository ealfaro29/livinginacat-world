import CoreGraphics
import CoreImage
import Foundation

// Dock positions are proposed only when the labelled app grid is present and
// the image contains icon-like contrast in at least two aligned bottom slots.
// Pixels are used locally and never written to disk.
struct DockDetector {
    struct Result { let slot: Int; let bounds: CGRect }
    static func detect(in source: CIImage, grid: [CGRect], context: CIContext) -> [Result] {
        guard !source.extent.isEmpty, grid.count >= 6 else { return [] }
        var columns: [[CGFloat]] = []
        for x in grid.map(\.midX).sorted() {
            if let i = columns.indices.first(where: { abs(columns[$0][0] - x) < 0.045 }) { columns[i].append(x) }
            else { columns.append([x]) }
        }
        columns = columns.filter { $0.count >= 2 }
        guard (3...5).contains(columns.count) else { return [] }
        let centers = columns.map { $0.reduce(0,+) / CGFloat($0.count) }.sorted()
        let widths = grid.map(\.width).sorted()
        let width = widths[widths.count / 2]
        let height = width * source.extent.width / source.extent.height
        guard (0.06...0.25).contains(width), (0.025...0.18).contains(height) else { return [] }

        let pixelWidth = 240
        let pixelHeight = max(240, min(720, Int((CGFloat(pixelWidth) * source.extent.height / source.extent.width).rounded())))
        let moved = source.transformed(by: CGAffineTransform(translationX: -source.extent.minX, y: -source.extent.minY))
        let scaled = moved.transformed(by: CGAffineTransform(scaleX: CGFloat(pixelWidth) / source.extent.width, y: CGFloat(pixelHeight) / source.extent.height))
        var data = [UInt8](repeating: 0, count: pixelWidth * pixelHeight * 4)
        context.render(scaled, toBitmap: &data, rowBytes: pixelWidth * 4, bounds: CGRect(x: 0, y: 0, width: pixelWidth, height: pixelHeight), format: .RGBA8, colorSpace: CGColorSpaceCreateDeviceRGB())

        func score(x: CGFloat, y: CGFloat) -> Double {
            var bright = 0, colorful = 0, sum = 0.0, sumSquared = 0.0, count = 0
            for iy in 0..<9 {
                for ix in 0..<9 {
                    let px = Int((x + (CGFloat(ix) / 8 - 0.5) * width * 0.64) * CGFloat(pixelWidth))
                    let py = pixelHeight - 1 - Int((y + (CGFloat(iy) / 8 - 0.5) * height * 0.64) * CGFloat(pixelHeight))
                    guard px >= 0, px < pixelWidth, py >= 0, py < pixelHeight else { continue }
                    let offset = (py * pixelWidth + px) * 4
                    let r = Int(data[offset]), g = Int(data[offset+1]), b = Int(data[offset+2])
                    let maxValue = max(r, max(g,b)), minValue = min(r, min(g,b))
                    if maxValue > 115 && (maxValue - minValue > 28 || minValue > 195) { bright += 1 }
                    if maxValue > 100 && maxValue - minValue > 32 { colorful += 1 }
                    let value = Double(r + g + b) / 3
                    sum += value; sumSquared += value * value; count += 1
                }
            }
            guard count > 0 else { return 0 }
            let variance = max(0, sumSquared / Double(count) - pow(sum / Double(count), 2))
            let filled = Double(bright) / Double(count), color = Double(colorful) / Double(count)
            guard filled >= 0.35, (color >= 0.12 || variance >= 650), variance >= 200 else { return 0 }
            return filled * min(1, variance / 1200)
        }
        var bestY: CGFloat = 0, bestScores: [Double] = [], bestValue = 0.0
        // Search the lower screen only; all dock slots should share one baseline.
        for step in 0...27 {
            let y = CGFloat(0.035 + Double(step) * 0.004)
            let scores = centers.map { score(x: $0, y: y) }
            let positives = scores.filter { $0 > 0 }
            guard positives.count >= 2 else { continue }
            let value = positives.reduce(0,+) * Double(positives.count)
            if value > bestValue { bestValue = value; bestY = y; bestScores = scores }
        }
        guard bestValue > 0 else { return [] }
        return centers.enumerated().compactMap { index, center in
            guard bestScores[index] > 0 else { return nil }
            return Result(slot: index + 1, bounds: CGRect(x: center - width/2, y: bestY - height/2, width: width, height: height))
        }
    }
}
