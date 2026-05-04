package cli

var campusRoutes = map[string]backendRoute{
	"canteens": {
		Path:        "/api/campus/canteens",
		Description: "List canteens.",
	},
	"canteen": {
		Path:        "/api/campus/canteens/{canteen_id}",
		PathArgs:    []string{"canteen_id"},
		Description: "Single canteen detail.",
	},
	"buildings": {
		Path:        "/api/campus/buildings",
		Description: "Campus buildings index.",
	},
	"building-detail": {
		Path:        "/api/campus/buildings/detail",
		Description: "Building detail. Use --query path=/campus-der-zukunft/....",
	},
	"events": {
		Path:        "/api/campus/events",
		Description: "Campus events. Optional queries: query, limit.",
	},
	"kuf": {
		Path:        "/api/campus/fitness/kuf",
		Description: "Current KuF training occupancy with local history.",
	},
	"seats": {
		Path:        "/api/campus/seats",
		Description: "Library seat availability.",
	},
}

func runCampus(args []string) int {
	return runBackendGroup("campus", args, campusRoutes)
}
