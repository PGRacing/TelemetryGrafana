/*
 * helper_func.h
 *
 *  Created on: Oct 20, 2022
 *      Author: Marcin
 */

#ifndef INC_HELPER_FUNC_H_
#define INC_HELPER_FUNC_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include "main.h"

typedef struct {
	float x;
	float y;
	float z;
} Vector_t;

typedef struct {
	float x;
	float y;
	float z;
} Vector2_t;

double clamp(double min, double max, double value);

double lerp(double min ,double max, double alpha);

double fastAbs(double x);

int8_t sign(double x);

double lowPassFilter(double input, double lastValue, double alpha);

uint16_t LittleToBigEndian(uint8_t* data);

void divideVariableInto1ByteArray(uint32_t* in, uint8_t* out, uint8_t size );

void UpdateRunTimeStats();

#ifdef __cplusplus
}
#endif

#endif /* INC_HELPER_FUNC_H_ */
