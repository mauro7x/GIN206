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
 *      Erbium (Er) REST Engine example.
 * \author
 *      Original: Matthias Kovatsch <kovatsch@inf.ethz.ch>
 *      Modifications: Mauro Parafati, Karla Friedrichs
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "contiki.h"
#include "contiki-net.h"
#include "rest-engine.h"

#include "dev/serial-line.h"

#include "resources/extern_var.h"

// Sensors data
int current_light = 256;
int current_temperature = 3;
float current_rain = 0.0f;
float current_traffic = 1.4f;
float current_accel = 0.0f;

// Alarms
int accel_alarm_status = 0;
int freezing_alarm_status = 0;
int traffic_alarm_status = 0;
int lights_alarm_status = 0;


#define DEBUG 0
#if DEBUG
#include <stdio.h>
#define PRINTF(...) printf(__VA_ARGS__)
#define PRINT6ADDR(addr) PRINTF("[%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x]", ((uint8_t *)addr)[0], ((uint8_t *)addr)[1], ((uint8_t *)addr)[2], ((uint8_t *)addr)[3], ((uint8_t *)addr)[4], ((uint8_t *)addr)[5], ((uint8_t *)addr)[6], ((uint8_t *)addr)[7], ((uint8_t *)addr)[8], ((uint8_t *)addr)[9], ((uint8_t *)addr)[10], ((uint8_t *)addr)[11], ((uint8_t *)addr)[12], ((uint8_t *)addr)[13], ((uint8_t *)addr)[14], ((uint8_t *)addr)[15])
#define PRINTLLADDR(lladdr) PRINTF("[%02x:%02x:%02x:%02x:%02x:%02x]", (lladdr)->addr[0], (lladdr)->addr[1], (lladdr)->addr[2], (lladdr)->addr[3], (lladdr)->addr[4], (lladdr)->addr[5])
#else
#define PRINTF(...)
#define PRINT6ADDR(addr)
#define PRINTLLADDR(addr)
#endif

/*
 * Resources to be activated need to be imported through the extern keyword.
 * The build system automatically compiles the resources in the corresponding sub-directory.
 */
extern resource_t
  res_event,

  // Alarms
  res_alarm_accel,
  res_alarm_freezing,
  res_alarm_lights,
  res_alarm_traffic,

  // Sensors
  res_sim_light,
  res_sim_temperature,
  res_sim_rain,
  res_sim_traffic,
  res_sim_accel;

extern char* res_serial_data;
PROCESS(er_example_server, "Resource CoAP Server");
AUTOSTART_PROCESSES(&er_example_server);

PROCESS_THREAD(er_example_server, ev, data)
{
  PROCESS_BEGIN();

  PROCESS_PAUSE();

  PRINTF("Starting Resource CoAP Server\n");

#ifdef RF_CHANNEL
  PRINTF("RF channel: %u\n", RF_CHANNEL);
#endif
#ifdef IEEE802154_PANID
  PRINTF("PAN ID: 0x%04X\n", IEEE802154_PANID);
#endif

  PRINTF("uIP buffer: %u\n", UIP_BUFSIZE);
  PRINTF("LL header: %u\n", UIP_LLH_LEN);
  PRINTF("IP+UDP header: %u\n", UIP_IPUDPH_LEN);
  PRINTF("REST max chunk: %u\n", REST_MAX_CHUNK_SIZE);

  /* Initialize the REST engine. */
  rest_init_engine();

  /*
   * Bind the resources to their Uri-Path.
   * WARNING: Activating twice only means alternate path, not two instances!
   * All static variables are the same for each URI path.
   */
  // Alarms
  rest_activate_resource(&res_alarm_accel, "my_res/alarm_accel");
  rest_activate_resource(&res_alarm_freezing, "my_res/alarm_freezing");
  rest_activate_resource(&res_alarm_lights, "my_res/alarm_lights");
  rest_activate_resource(&res_alarm_traffic, "my_res/alarm_traffic");
  // Sensors
  rest_activate_resource(&res_sim_light, "my_res/sim_light");
  rest_activate_resource(&res_sim_temperature, "my_res/sim_temperature");
  rest_activate_resource(&res_sim_rain, "my_res/sim_rain");
  rest_activate_resource(&res_sim_traffic, "my_res/sim_traffic");
  rest_activate_resource(&res_sim_accel, "my_res/sim_accel");

  /* Define application-specific events here. */
  while(1) {
    PROCESS_WAIT_EVENT();
    if(ev == serial_line_event_message) {
      res_serial_data = (char*)data;

      /* Call the event_handler for this application-specific event. */
      res_event.trigger();

      /* Also call the separate response example handler. */
      // res_separate.resume();
    }
  }                             /* while (1) */

  PROCESS_END();
}
