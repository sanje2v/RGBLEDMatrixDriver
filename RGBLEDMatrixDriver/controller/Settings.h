#ifndef SETTINGS_H
#define SETTINGS_H

#define SERIAL_BAUD_RATE                      57600          // CAUTION: Some chips may not support this baud rate, so test
#define READY_MESSAGE                         F("READY\r\n")  // To notify host, controller is ready
#define SYNC_MESSAGE                          F("SYNC\r\n")   // To notify host, to send frame data
#define STOP_MESSAGE                          F("STOP\r\n")   // To notify host, to stop sending frame data

#define NUM_LED_MATRICES                      4
#define NUM_ROWS_PER_MATRIX                   8
#define NUM_COLS_PER_MATRIX                   8
#define NUM_COLOR_CHANNELS                    3
#define TOTAL_LEDS                            (NUM_LED_MATRICES * NUM_ROWS_PER_MATRIX * NUM_COLS_PER_MATRIX)
#define ONE_FRAME_SIZE                        (NUM_COLOR_CHANNELS * TOTAL_LEDS)
#define TOTAL_FRAMES                          20              // This value is dependent on free RAM available
#define TOTAL_FRAMES_BUFFER_SIZE              (TOTAL_FRAMES * ONE_FRAME_SIZE)   // NOTE: For 4 matrices, this allows for 12 frames
#define LED_MATRICES_PWM_PIN                  0               // NOTE: Called P0 but actually is the first pin
#define FRAMES_TO_WRITE_AHEAD                 2               // In state reinitialized, position write pointer ahead to amount
#define TIME_BETWEEN_FRAMES_MS                500
#define TIME_DELAY_CLEAR_RX_BUFFER_CHECK_MS   10

#endif
