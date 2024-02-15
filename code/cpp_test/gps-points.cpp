/*
 * gps_tracker.c
 *
 *  Created on: 23 Feb, 2023
 *      Author: Marcin Nadarzyński
 */

#include "gps_tracker.h"
#include "cmsis_os.h"
#include "eeprom.h"
#include "helper_func.h"
#include "i2c.h"
#include "FreeRTOS.h"
#include "semphr.h"
#include "structs/telemetry_data.h"
#include "structs/vector.h"
#include <math.h>

extern osSemaphoreId_t newVehiclePositionHandle;

static float calculateInterpolatedTime(GPS_Point_t *currentPosition,
		GPS_Point_t *firstPoint, GPS_Point_t *secondPoint);
static double calculateDistance(double x1, double y1, double x2, double y2);

void recordFirstLap(GPS_TrackInfo_t *trackInfo)
{
	uint32_t firstPointTimestamp = 0;
	uint8_t isLapFinished = 0;
	GPS_Point_t *newVehiclePosition;
	GPS_Point_t *lastVehiclePosition;

	if (xSemaphoreTake(newVehiclePositionHandle, (TickType_t) HAL_MAX_DELAY))
	{
		trackInfo->bestLap = pvPortMalloc(sizeof(GPS_Point_t));
		trackInfo->bestLap->lon = telemetryData.vehiclePosition.lon;
		trackInfo->bestLap->lat = telemetryData.vehiclePosition.lat;
		trackInfo->bestLap->timestamp = 0;
		trackInfo->bestLap->nextPoint = NULL;
		trackInfo->bestLap->prevPoint = NULL;

		firstPointTimestamp = telemetryData.vehiclePosition.timestamp;
		lastVehiclePosition = trackInfo->bestLap;
		trackInfo->pointsNumber = 1;
	}

	while (isLapFinished == 0)
	{
		if (xSemaphoreTake(newVehiclePositionHandle,
				(TickType_t) HAL_MAX_DELAY))
		{
			newVehiclePosition = pvPortMalloc(sizeof(GPS_Point_t));
			newVehiclePosition->lon = telemetryData.vehiclePosition.lon;
			newVehiclePosition->lat = telemetryData.vehiclePosition.lat;
			newVehiclePosition->timestamp =
					telemetryData.vehiclePosition.timestamp
							- firstPointTimestamp;
			newVehiclePosition->nextPoint = NULL;
			newVehiclePosition->prevPoint = lastVehiclePosition;

			lastVehiclePosition->nextPoint = newVehiclePosition;
			lastVehiclePosition = newVehiclePosition;
			trackInfo->pointsNumber++;
		}
	}
}

float calculateGainLoss(GPS_TrackInfo_t *trackInfo,
		GPS_Point_t *newVehiclePosition)
{
	static GPS_Point_t *lastUsedPoint = NULL;
	GPS_Point_t *firstPoint = NULL;
	GPS_Point_t *secondPoint = NULL;
	float interpolatedTime = 0.0f;
	float deltaTime = nanf("1");
	uint8_t failedTries = 0;
	if (lastUsedPoint == NULL)
	{
		if (trackInfo->bestLap != NULL)
		{
			lastUsedPoint = trackInfo->bestLap;
		}
		else
		{
			return deltaTime;
		}
	}

	if (newVehiclePosition->distance < lastUsedPoint->distance)
	{
		firstPoint = lastUsedPoint->prevPoint;
		secondPoint = lastUsedPoint;
	}
	else
	{
		firstPoint = lastUsedPoint;
		secondPoint = lastUsedPoint->nextPoint;
	}
	interpolatedTime = calculateInterpolatedTime(newVehiclePosition, firstPoint,
			secondPoint);

	while (interpolatedTime == -1.0f && failedTries < 5)
	{
		interpolatedTime = calculateInterpolatedTime(newVehiclePosition,
				firstPoint, secondPoint);
		failedTries++;
	}

	if (failedTries != 5)
	{
		lastUsedPoint = secondPoint;
	}
	deltaTime = newVehiclePosition->timestamp - interpolatedTime;

	return deltaTime;
}

static float calculateInterpolatedTime(GPS_Point_t *currentPosition,
		GPS_Point_t *firstPoint, GPS_Point_t *secondPoint)
{
	const float a1 = (firstPoint->lat - secondPoint->lat)
			/ (firstPoint->lon - secondPoint->lon);
	const float b1 = firstPoint->lat - a1 * firstPoint->lon;

	const float a2 = 1 / a1;
	const float b2 = currentPosition->lat - a2 * currentPosition->lon;

	const float xC = (b1 - b2) / (a2 - a1);
	const float yC = a2 * xC + b2;

	const float maxDistance = calculateDistance(firstPoint->lon,
			firstPoint->lat, secondPoint->lon, secondPoint->lat);
	const float partDistance1 = calculateDistance(firstPoint->lon,
			firstPoint->lat, xC, yC);
	const float partDistance2 = calculateDistance(secondPoint->lon,
			secondPoint->lat, xC, yC);

	if (partDistance1 + partDistance2 <= maxDistance * 1.01
			&& partDistance1 + partDistance2 >= maxDistance * 0.99)
	{
		return lerp(firstPoint->timestamp, secondPoint->timestamp,
				partDistance1 / maxDistance);
	}

	return -1.0f;
}

static double calculateDistance(double x1, double y1, double x2, double y2)
{
	return sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2));
}

void serializeLap(GPS_TrackInfo_t *trackInfo)
{
	GPS_Point_t *currentPoint = trackInfo->bestLap;
	const uint8_t devAddr = EEPROM_BASE_DEV_ADDRESS | EEPROM_WRITE;
	uint16_t counter = 0;

	while (counter < trackInfo->pointsNumber && currentPoint->nextPoint != NULL)
	{
		uint32_t memoryAddress =
		EEPROM_SETTINGS_SIZE + counter * sizeof(GPS_Point_t)
				+ sizeof(GPS_TrackInfo_t);

		HAL_I2C_Mem_Write_IT(&hi2c3,
				devAddr | ((memoryAddress & EEPROM_PAGE_SIZE) > 8),
				memoryAddress & 0x00FF,
				EEPROM_PAGE_SIZE, (uint8_t*) currentPoint, sizeof(GPS_Point_t));

		currentPoint = currentPoint->nextPoint;
		vPortFree(currentPoint->prevPoint);
		counter++;
	}
	vPortFree(currentPoint);

	HAL_I2C_Mem_Write_IT(&hi2c3,
			devAddr | ((EEPROM_SETTINGS_SIZE & EEPROM_PAGE_SIZE) > 8),
			EEPROM_SETTINGS_SIZE & 0x00FF,
			EEPROM_PAGE_SIZE, (uint8_t*) trackInfo, sizeof(trackInfo));
}

uint8_t deserializeLap(GPS_TrackInfo_t *outTrackInfo)
{
	GPS_Point_t *newPoint = NULL;
	GPS_Point_t *lastPoint = NULL;
	const uint8_t devAddr = EEPROM_BASE_DEV_ADDRESS | EEPROM_WRITE;
	uint8_t isSuccess = 1;
	if (outTrackInfo == NULL)
	{
		outTrackInfo = (GPS_TrackInfo_t*) pvPortMalloc(sizeof(GPS_TrackInfo_t));
	}
	HAL_I2C_Mem_Read_IT(&hi2c3,
			devAddr | ((EEPROM_SETTINGS_SIZE & EEPROM_PAGE_SIZE) > 8),
			EEPROM_SETTINGS_SIZE & 0x00FF,
			EEPROM_PAGE_SIZE, (uint8_t*) &outTrackInfo,
			sizeof(GPS_TrackInfo_t));

	if (outTrackInfo->pointsNumber != 0)
	{
		outTrackInfo->bestLap = (GPS_Point_t*) pvPortMalloc(
				sizeof(GPS_Point_t));
		HAL_I2C_Mem_Read_IT(&hi2c3,
				devAddr | ((EEPROM_SETTINGS_SIZE & EEPROM_PAGE_SIZE) > 8),
				EEPROM_SETTINGS_SIZE & 0x00FF,
				EEPROM_PAGE_SIZE, (uint8_t*) outTrackInfo->bestLap,
				sizeof(GPS_Point_t));
		lastPoint = outTrackInfo->bestLap;

		for (uint16_t i = 1; i < outTrackInfo->pointsNumber; i++)
		{
			uint32_t memoryAddress = EEPROM_SETTINGS_SIZE
					+ i * sizeof(GPS_Point_t) + sizeof(GPS_TrackInfo_t);
			newPoint = (GPS_Point_t*) pvPortMalloc(sizeof(GPS_Point_t));

			HAL_I2C_Mem_Read_IT(&hi2c3,
					devAddr | ((memoryAddress & EEPROM_PAGE_SIZE) > 8),
					memoryAddress & 0x00FF,
					EEPROM_PAGE_SIZE, (uint8_t*) newPoint, sizeof(GPS_Point_t));

			lastPoint->nextPoint = newPoint;
			newPoint->prevPoint = lastPoint;
			lastPoint = newPoint;
		}
	}
	else
	{
		isSuccess = 0;
	}

	return isSuccess;
}

float isVehicleCrossedFinishLine(GPS_Point_t *prevVehiclePosition,
		GPS_Point_t *newVehiclePosition, GPS_Point_t *finishLine[])
{
	const float a1 = prevVehiclePosition->lon * newVehiclePosition->lat
			- prevVehiclePosition->lat * newVehiclePosition->lon;
	const float a2 = finishLine[0]->lon * finishLine[1]->lat
			- finishLine[0]->lat * finishLine[1]->lon;

	const float b1 = prevVehiclePosition->lon - newVehiclePosition->lon;
	const float b2 = finishLine[0]->lon - finishLine[1]->lon;

	const float c1 = prevVehiclePosition->lat - newVehiclePosition->lat;
	const float c2 = finishLine[0]->lat - finishLine[1]->lat;

	const float d = (b1 * c2 - c1 * b2);
	Vector2F crossingPoint;
	crossingPoint.x = (a1 * b2 - b1 * a2) / d;
	crossingPoint.y = (a1 * c2 - c1 - a2) / d;

	const float maxDistance = calculateDistance(finishLine[0]->lon,
			finishLine[0]->lat, finishLine[1]->lon, finishLine[1]->lat);
	const float partDistance1 = calculateDistance(crossingPoint.x,
			crossingPoint.y, finishLine[0]->lon, finishLine[0]->lat);
	const float partDistance2 = calculateDistance(crossingPoint.x,
			crossingPoint.y, finishLine[1]->lon, finishLine[1]->lat);

	if (partDistance1 + partDistance2 <= maxDistance * 1.01
			&& partDistance1 + partDistance2 >= maxDistance * 0.99)
	{
		const float lastVehicleToFinishLine = calculateDistance(crossingPoint.x,
				crossingPoint.y, prevVehiclePosition->lon,
				prevVehiclePosition->lat);
		const float pointsDistance = calculateDistance(prevVehiclePosition->lon,
				prevVehiclePosition->lat, newVehiclePosition->lon,
				newVehiclePosition->lat);

		return lerp(prevVehiclePosition->timestamp,
				newVehiclePosition->timestamp,
				lastVehicleToFinishLine / pointsDistance);
	}

	return -1.0f;
}