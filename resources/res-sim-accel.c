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
 *      Template: Matthias Kovatsch <kovatsch@inf.ethz.ch>
 *	Modifications: Mauro Parafati, Karla Friedrichs
 */

#include <stdlib.h>
#include <string.h>
#include "rest-engine.h"

#include "extern_var.h"

static void sim_accel_get_handler(void *request, void *response, uint8_t *buffer, uint16_t preferred_size, int32_t *offset);
static float get_accel_sensor_value();
static int in_decrease_range(int random);
static int in_increase_range(int random);
static int min_not_reached();
static int max_not_reached();
static void decrease();
static void increase();

static const int PROB_DECREASE = 50; // in percent
static const int PROB_INCREASE = 5;
static const int MIN_ACCEL = 0.0;
static const int MAX_ACCEL = 2.0;


RESOURCE(res_sim_accel,
         "title=SIM-ACCELERATION",
         sim_accel_get_handler,
         NULL,
         NULL,
         NULL);

static void
sim_accel_get_handler(void *request, void *response, uint8_t *buffer, uint16_t preferred_size, int32_t *offset)
{
  float accel_sensor_value = get_accel_sensor_value();
  REST.set_header_content_type(response, REST.type.TEXT_PLAIN);
  snprintf((char*)buffer, REST_MAX_CHUNK_SIZE, "%f", accel_sensor_value);
  REST.set_response_payload(response, (int *)buffer, strlen((char *)buffer));
}


static float
get_accel_sensor_value()
{
  // randomly change the value, with a preference of staying in the same state
  int random = 0;
  random = rand() % 100;

  // increase or decrease acceleration exponentially, but don't exceed bounds
  if (in_decrease_range(random)) {
    if (min_not_reached()) {
      decrease();
    }
  } else if (in_increase_range(random)) {
    if (max_not_reached()) {
      increase();
    }
  }
  return current_accel;
}

static int
in_decrease_range(int random) {
  return random < PROB_DECREASE;
}

static int
in_increase_range(int random) {
  return random >= 100 - PROB_INCREASE;
}

static int
min_not_reached() {
  return current_accel > MIN_ACCEL;
}

static int
max_not_reached() {
  return current_accel < MAX_ACCEL;
}

static void
decrease() {
  if (current_accel - 0.2 > MIN_ACCEL) {
    current_accel = current_accel - 0.2;
  } else {
    current_accel = MIN_ACCEL;
  }
}

static void
increase() {
  if (current_accel + 0.5 < MAX_ACCEL) {
    current_accel = current_accel + 0.5;
  } else {
    current_accel = MAX_ACCEL;
  }
}