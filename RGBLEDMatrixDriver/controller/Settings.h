#ifndef SETTINGS_H
#define SETTINGS_H

#define SERIAL_BAUD_RATE                      115200        // CAUTION: Some chips may not support this baud rate, so test
#define READY_MESSAGE                         F("READY\r\n")
#define SYNC_MESSAGE                          F("SYNC\r\n")

#define NUM_LED_MATRICES                      4
#define NUM_ROWS_PER_MATRIX                   8
#define NUM_COLS_PER_MATRIX                   8
#define NUM_COLOR_CHANNELS                    3
#define TOTAL_LEDS                            (NUM_ROWS_PER_MATRIX * NUM_COLS_PER_MATRIX)
#define ONE_MATRIX_FRAME_SIZE                 (TOTAL_LEDS * NUM_COLOR_CHANNELS)
#define ONE_FRAME_SIZE                        (NUM_LED_MATRICES * ONE_MATRIX_FRAME_SIZE)
#define TOTAL_FRAMES                          20            // This value is dependent on free RAM available
#define TOTAL_FRAMES_BUFFER_SIZE              (TOTAL_FRAMES * ONE_FRAME_SIZE)   // NOTE: For 4 matrices, this allows for 12 frames
#define LED_MATRICES_PWM_PIN                  0             // NOTE: Called P0 but actually is the first pin
#define FRAMES_TO_WRITE_AHEAD                 2             // In state reinitialized, position write pointer ahead to amount
#define TIME_BETWEEN_FRAMES_MS                500

#endif
