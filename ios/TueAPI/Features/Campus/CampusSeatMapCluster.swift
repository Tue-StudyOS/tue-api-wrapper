import CoreGraphics

struct CampusSeatMapCluster: Identifiable {
    let points: [CampusSeatMapPoint]

    var id: CampusSeatMapPoint { anchor }
    var anchor: CampusSeatMapPoint { points[0] }

    static func layout(
        _ points: [CampusSeatMapPoint],
        badgeSize: CGSize,
        project: (CampusSeatMapPoint) -> CGPoint?
    ) -> [Self] {
        var groups: [(points: [CampusSeatMapPoint], bounds: CGRect)] = []
        for point in points {
            guard let pixel = project(point), pixel.x.isFinite, pixel.y.isFinite else { continue }
            let bounds = CGRect(x: pixel.x - badgeSize.width / 2, y: pixel.y - badgeSize.height,
                                width: badgeSize.width, height: badgeSize.height)
            if let index = groups.firstIndex(where: { $0.bounds.intersects(bounds) }) {
                groups[index].points.append(point)
            } else {
                groups.append(([point], bounds))
            }
        }
        return groups.map { Self(points: $0.points) }
    }
}
