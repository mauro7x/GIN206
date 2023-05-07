/*
 * Copyright (c) 2013, Institute for Pervasive Computing, ETH Zurich
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the Institute nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE INSTITUTE AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE INSTITUTE OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 * This file is part of the Contiki operating system.
 */

/**
 * \file
 *      Simulation of an accelerator resource.
 * \author
 *      Template:   Matthias Kovatsch <kovatsch@inf.ethz.ch>
 *                  Cristiano De Alti <cristiano_dealti@hotmail.com>
 *	    Modifications: Mauro Parafati, Karla Friedrichs
 */

#include "contiki.h"

#include <limits.h>
#include <stdlib.h>
#include <string.h>
#include "rest-engine.h"

#include "extern_var.h"
#include "res-sim-temperature.h"

static void res_get_handler(void *request, void *response, uint8_t *buffer, uint16_t preferred_size, int32_t *offset);
static void res_periodic_handler(void);
static int freezing_alarm_threshold_reached();

#define MAX_AGE                   60
#define FREEZING_ALARM_FREQ_SECS  60

static const int TEMP_THRESHOLD = 2;

PERIODIC_RESOURCE(res_alarm_freezing,
         "title=ALARM-FREEZING",
         res_get_handler,
         NULL,
         NULL,
         NULL,
         CLOCK_SECOND * FREEZING_ALARM_FREQ_SECS,
         res_periodic_handler);

static void
res_get_handler(void *request, void *response, uint8_t *buffer, uint16_t preferred_size, int32_t *offset)
{
  printf("[res-alarm-freezing] res_get_handler called (status=%d)\n", freezing_alarm_status);

  REST.set_header_content_type(response, REST.type.TEXT_PLAIN);
  snprintf((char *)buffer, REST_MAX_CHUNK_SIZE, "%d", freezing_alarm_status);
  REST.set_response_payload(response, (uint8_t *)buffer, strlen((char *)buffer));
  REST.set_header_max_age(response, MAX_AGE);

  /* The REST.subscription_handler() will be called for observable resources by the REST framework. */
}

/*
 * Additionally, a handler function named [resource name]_handler must be implemented for each PERIODIC_RESOURCE.
 * It will be called by the REST manager process with the defined period.
 */
static void
res_periodic_handler()
{
  // Ignore alarm if not moving
  if (accel_alarm_status == 0) {
    return;
  }
  
  printf("[res-alarm-freezing] res_periodic_handler called (status=%d)\n", freezing_alarm_status);

  // update alarm status
  int new_alarm_status = freezing_alarm_threshold_reached();
  if (new_alarm_status != freezing_alarm_status) {
    freezing_alarm_status = new_alarm_status;
  
    printf("[res-alarm-freezing] status changed to %d, notifying subscribers\n", freezing_alarm_status);
    /* Notify the registered observers which will trigger the res_get_handler to create the response. */
    REST.notify_subscribers(&res_alarm_freezing);
  }
}

static int
freezing_alarm_threshold_reached()
{
  // get a fresh sensor value
  // the extern variable current_temperature could be used directly if it was updated more frequently, but in this
  // architecture it is only updated upon external GET
  int freezing_sensor_value = get_temperature_sensor_value();
  return freezing_sensor_value <= TEMP_THRESHOLD;
}