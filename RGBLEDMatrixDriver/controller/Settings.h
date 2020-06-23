#ifndef Settings_h
#define Settings_h

// SETTINGS
//#define PRINT_MILLIS_PER_FRAME      // NOTE: Uncomment this line to print milliseconds that a frame is shown to serial

#define LED_COLOR_ON                          (byte)0xFF    // NOTE: This is valid for EP-005 LED matrix
#define LED_COLOR_OFF                         (byte)0x00    // NOTE: This is valid for EP-005 LED matrix
#define SERIAL_SPEED_BPS                      57600		      // CAUTION: Some chips may not support this baud rate, set this to the gighest for you
#define RESET_COMMAND                         "RESET\r\n"
#define RESET_COMMAND_SIZE                    7
#define NUM_LED_MATRICES                      4
#define NUM_ROWS_PER_MATRIX                   8
#define NUM_COLS_PER_MATRIX                   8
#define NUM_COLORS_PER_ROW_DOT                3
#define TOTAL_LEDS                            (NUM_ROWS_PER_MATRIX * NUM_COLS_PER_MATRIX)
#define ONE_MATRIX_FRAME_SIZE                 (TOTAL_LEDS * NUM_COLORS_PER_ROW_DOT)
#define ONE_FRAME_SIZE                        (NUM_LED_MATRICES * ONE_MATRIX_FRAME_SIZE)
#define TOTAL_FRAMES                          20                    // This value is dependent on free RAM available
#define TOTAL_FRAME_BUFFER_SIZE               (TOTAL_FRAMES * ONE_FRAME_SIZE)   // NOTE: For 4 matrices, this allows for 12 frames
#define LED_MATRICES_PWM_PIN                  3   // Called P3 but actually is the first pin
#define UART_RX_PIN                           14  // Called P14
#define UART_TX_PIN                           15  // Called P15
//#define NUM_REDRAW_EACH_FRAME                 118                   // NOTE: This value alters milliseconds to per frame and here is set to 100 ms
//#define _LEDMATRIX_SELECT_PINS								{ 10, 11, 12, 13 }    // CAUTION: Make sure the number of pins match 'NUM_LED_MATRICES'
//16
#endif
