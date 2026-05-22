package seatfinder

import (
	"sync"
	"time"
)

var (
	tzOnce sync.Once
	tzLoc  *time.Location
)

func germanLocation() *time.Location {
	tzOnce.Do(func() {
		loc, err := time.LoadLocation("Europe/Berlin")
		if err != nil {
			tzLoc = time.Local
			return
		}
		tzLoc = loc
	})
	return tzLoc
}
