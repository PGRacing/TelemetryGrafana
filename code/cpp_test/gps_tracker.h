/*
 * gps_tracker.h
 *
 *  Created on: 23 Feb 2023
 *      Author: Marcin Nadarzyński
 */

#ifndef INC_GPS_TRACKER_H_
#define INC_GPS_TRACKER_H_

#include <sys/_stdint.h>

typedef struct
{
	float lon;
	float lat;
	uint32_t timestamp;
} GPS_PointShort_t;


typedef struct GPS_Point_t GPS_Point_t;

typedef struct
{
	uint16_t pointsNumber;
	char trackName[100];
	GPS_Point_t *bestLap;
	GPS_Point_t *lastLap;
	GPS_PointShort_t *finishPoints[2];
} GPS_TrackInfo_t;

struct GPS_Point_t
{
	float lon;
	float lat;
	uint16_t distance;
	uint32_t timestamp;
	GPS_Point_t *nextPoint;
	GPS_Point_t *prevPoint;
};


void recordFirstLap(GPS_TrackInfo_t *trackInfo);
float calculateGainLoss();

void serializeLap(GPS_TrackInfo_t *trackInfo);
uint8_t deserializeLap(GPS_TrackInfo_t *outTrackInfo);

float isVehicleCrossedFinishLine(GPS_Point_t *prevVehiclePosition,
		GPS_Point_t *newVehiclePosition, GPS_Point_t* finishLine[]);
#endif /* INC_GPS_TRACKER_H_ */
