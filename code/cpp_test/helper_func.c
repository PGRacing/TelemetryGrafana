/*
 * helper_func.c
 *
 *  Created on: Oct 20, 2022
 *      Author: Marcin
 */

#include "helper_func.h"
#include "FreeRTOS.h"
#include "structs/display_data.h"
#include "task.h"
#include <string.h>

double lerp(double A, double B, double Alpha)
{
	return A + Alpha * (B - A);
}

double clamp(double min, double max, double value)
{
	return value > min ? (value < max ? value : max) : min;
}

double fastAbs(double x)
{
	return x < 0.0f ? -x : x;
}

int8_t sign(double x)
{
	return x > 0.0f ? 1 : (x < 0.0f ? -1 : 0);
}

double lowPassFilter(double input, double lastValue, double alpha)
{
	return (1.0f - alpha) * input + alpha * lastValue;
}

uint16_t LittleToBigEndian(uint8_t *data)
{
	uint16_t returnData = data[0] + (data[1] << 8);
	return returnData;
}

void divideVariableInto1ByteArray(uint32_t *in, uint8_t *out, uint8_t size)
{
	for (uint8_t i = 0; i < size; i++)
	{
		out[i] = *in % 0x100;
		*in /= 0x100;
	}
}

void UpdateRunTimeStats()
{
	TaskStatus_t *pxTaskStatusArray;
	UBaseType_t uxArraySize, x;
	uint32_t ulTotalTime, ulStatsAsPercentage;

	uxArraySize = uxTaskGetNumberOfTasks();

	/* Allocate an array index for each task.  NOTE!  If
	 configSUPPORT_DYNAMIC_ALLOCATION is set to 0 then pvPortMalloc() will
	 equate to NULL. */
	pxTaskStatusArray = pvPortMalloc(
			uxTaskGetNumberOfTasks() * sizeof(TaskStatus_t));

	if (pxTaskStatusArray != NULL)
	{
		/* Generate the (binary) data. */
		uxArraySize = uxTaskGetSystemState(pxTaskStatusArray, uxArraySize,
				&ulTotalTime);

		/* For percentage calculations. */
		ulTotalTime /= 100UL;

		/* Avoid divide by zero errors. */
		if (ulTotalTime > 0UL)
		{
			/* Create a human readable table from the binary data. */
			for (x = 0; x < uxArraySize; x++)
			{
				/* What percentage of the total run time has the task used?
				 This will always be rounded down to the nearest integer.
				 ulTotalRunTimeDiv100 has already been divided by 100. */
				ulStatsAsPercentage = pxTaskStatusArray[x].ulRunTimeCounter
						/ ulTotalTime;

				if (strcmp(pxTaskStatusArray[x].pcTaskName, (char*)"hardwareTask")==0)
				{
					displayInfo.hardwareTaskCPUUtilization =
							ulStatsAsPercentage;
				}
				else if (strcmp(pxTaskStatusArray[x].pcTaskName, (char*)"RPMLed")==0)
				{
					displayInfo.RPMLedTaskCPUUtilization = ulStatsAsPercentage;
				}
				else if (strcmp(pxTaskStatusArray[x].pcTaskName,
						(char*)"touchGFXTask")==0)
				{
					displayInfo.touchGFXTaskCPUUtilization =
							ulStatsAsPercentage;
				}
				else if (strcmp(pxTaskStatusArray[x].pcTaskName,
						(char*)"statusLedTask")==0)
				{
					displayInfo.statusLedTaskCPUUtilization =
							ulStatsAsPercentage;
				}
				else if (strcmp(pxTaskStatusArray[x].pcTaskName,
						(char*)"displayBackligh")==0)
				{
					displayInfo.displayBacklighTaskCPUUtilization =
							ulStatsAsPercentage;
				}
				else if (strcmp(pxTaskStatusArray[x].pcTaskName, (char*)"IDLE")==0)
				{
					displayInfo.idleTaskCPUUtilization = ulStatsAsPercentage;
				}

			}
		}

		/* Free the array again.  NOTE!  If configSUPPORT_DYNAMIC_ALLOCATION
		 is 0 then vPortFree() will be #defined to nothing. */
		vPortFree(pxTaskStatusArray);
	}
}

