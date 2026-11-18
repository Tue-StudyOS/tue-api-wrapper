import WidgetKit
import SwiftUI

@main
struct TueAPIWidgetBundle: WidgetBundle {
    var body: some Widget {
        UpcomingLecturesWidget()
        KufOccupancyWidget()
        KufPassWidget()
        LectureLiveActivityWidget()
    }
}
