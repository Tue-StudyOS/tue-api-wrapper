package cli

var discoveryRoutes = map[string]backendRoute{
	"search": {
		Path:        "/api/discovery/courses/search",
		Description: "Local semantic course discovery. Optional queries: q, source, kind, degree, module_code, term, tag, include_private, limit.",
	},
	"refresh": {
		Method:      "POST",
		Path:        "/api/discovery/courses/refresh",
		Description: "Refresh the local course discovery index. Optional queries: q, include_private, limit.",
	},
	"status": {
		Path:        "/api/discovery/courses/status",
		Description: "Current local course discovery index status.",
	},
}

func runDiscovery(args []string) int {
	return runBackendGroup("discovery", args, discoveryRoutes)
}
