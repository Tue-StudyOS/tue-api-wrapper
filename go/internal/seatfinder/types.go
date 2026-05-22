package seatfinder

type SeatLocationStatus struct {
	LocationID       string   `json:"location_id"`
	Name             string   `json:"name"`
	LongName         *string  `json:"long_name"`
	Level            *string  `json:"level"`
	Building         *string  `json:"building"`
	Room             *string  `json:"room"`
	TotalSeats       *int     `json:"total_seats"`
	FreeSeats        *int     `json:"free_seats"`
	OccupiedSeats    *int     `json:"occupied_seats"`
	OccupancyPercent *float64 `json:"occupancy_percent"`
	UpdatedAt        *string  `json:"updated_at"`
	URL              *string  `json:"url"`
	GeoCoordinates   *string  `json:"geo_coordinates"`
}

type SeatAvailabilityResponse struct {
	SourceURL   string               `json:"source_url"`
	RetrievedAt string               `json:"retrieved_at"`
	Locations   []SeatLocationStatus `json:"locations"`
}
