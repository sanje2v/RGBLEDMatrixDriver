using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.IO.Ports;

namespace WindowsFormsApp1
{
    public partial class Form1 : Form
    {
        private static int NUM_FRAMES = 12;
        private static int ONE_FRAME_SIZE = 96;
        private static int NUM_COLORS_PER_DOT = 3;
        private static string CONTROLLER_INITIALIZED_MESSAGE = "INITIALIZED";
        private static string CONTROLLER_RESET_COMMAND = "RESET";

        private List<byte> FRAMES;
        private Thread thread_worker;
        private ManualResetEventSlim thread_worker_signal;
        private bool isControllerInitialized;
        private Queue<Action> gui_dispatcher_queue;


        private static void thread_worker_func(object _Form1)
        {
            string getNextMessageAndWriteOut(Form1 __this, SerialPort serialToController)
            {
                string message = String.Copy(serialToController.ReadLine());
                __this.gui_dispatcher_queue.Enqueue(() => __this.txt_serialoutput.AppendText(message + Environment.NewLine));

                return message;
            }

            Form1 _this = (Form1)_Form1;

            for (int i = 0; i < NUM_FRAMES; ++i)
            {
                for (int j = 0; j < ONE_FRAME_SIZE; j += NUM_COLORS_PER_DOT)
                {
                    if (i < 3)
                    {
                        _this.FRAMES[i * ONE_FRAME_SIZE + j + 0] = 0x00;
                        _this.FRAMES[i * ONE_FRAME_SIZE + j + 2] = 0xFF;
                        _this.FRAMES[i * ONE_FRAME_SIZE + j + 1] = 0xFF;
                    }
                    else if (i < 6)
                    {
                        _this.FRAMES[i * ONE_FRAME_SIZE + j + 0] = 0xFF;
                        _this.FRAMES[i * ONE_FRAME_SIZE + j + 2] = 0x00;
                        _this.FRAMES[i * ONE_FRAME_SIZE + j + 1] = 0xFF;
                    }
                    else if (i < 9)
                    {
                        _this.FRAMES[i * ONE_FRAME_SIZE + j + 0] = 0xFF;
                        _this.FRAMES[i * ONE_FRAME_SIZE + j + 2] = 0xFF;
                        _this.FRAMES[i * ONE_FRAME_SIZE + j + 1] = 0x00;
                    }
                    else
                    {
                        _this.FRAMES[i * ONE_FRAME_SIZE + j + 0] = 0xFF;
                        _this.FRAMES[i * ONE_FRAME_SIZE + j + 2] = 0x00;
                        _this.FRAMES[i * ONE_FRAME_SIZE + j + 1] = 0x00;
                    }
                }
            }

            Debug.Assert(_this.FRAMES.Count % ONE_FRAME_SIZE == 0);

            try
            {
                using (var serialToController = new SerialPort("COM1", 57600, Parity.None, 8, StopBits.One))
                {
                    //serialToController.ReadTimeout = 1000;
                    //serialToController.WriteTimeout = 1000;

                    serialToController.Open();
                    serialToController.NewLine = "\r\n";

                    serialToController.DiscardInBuffer();
                    serialToController.DiscardOutBuffer();

                    // Ask controller to reset
                    serialToController.WriteLine(CONTROLLER_RESET_COMMAND);
                    _this.gui_dispatcher_queue.Enqueue(() => _this.lbl_status.Text = "Reset sent. Waiting for initializing message from controller.");

                    // Set the index in FRAME of next frame
                    var next_frame_start_position = 0;

                    while (!_this.thread_worker_signal.IsSet)
                    {
                        if (serialToController.BytesToRead > 0)
                        {
                            var message = getNextMessageAndWriteOut(_this, serialToController);

                            if (!_this.isControllerInitialized && message.Equals(CONTROLLER_INITIALIZED_MESSAGE))
                            {
                                _this.isControllerInitialized = true;
                                _this.gui_dispatcher_queue.Enqueue(() => _this.lbl_status.Text = "Controller initialized. Ready.");
                            }
                            else if (_this.isControllerInitialized && message.StartsWith("SYNC"))
                            {
                                serialToController.Write(_this.FRAMES.ToArray(), next_frame_start_position, ONE_FRAME_SIZE);
                                next_frame_start_position = (next_frame_start_position + ONE_FRAME_SIZE) % _this.FRAMES.Count;

                                bool hasErrorOccurred = false;
                                while (true)
                                {
                                    message = getNextMessageAndWriteOut(_this, serialToController);
                                    if (message.StartsWith("OK"))
                                        break;
                                    else if (message.StartsWith("ERROR"))
                                    {
                                        _this.gui_dispatcher_queue.Enqueue(() => _this.lbl_status.Text = "Error occurred!");
                                        _this.isControllerInitialized = false;
                                        hasErrorOccurred = true;
                                        break;
                                    }
                                }

                                if (hasErrorOccurred)
                                    break;
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                var ex_str = "Exception occurred: " + ex.Message.ToString();
                _this.gui_dispatcher_queue.Enqueue(() => _this.lbl_status.Text = ex_str);
            }
        }

        public Form1()
        {
            InitializeComponent();

            this.FRAMES = new List<byte>(Form1.NUM_FRAMES * Form1.ONE_FRAME_SIZE);
            for (int i = 0; i < (Form1.NUM_FRAMES * Form1.ONE_FRAME_SIZE); ++i)
                this.FRAMES.Add(0xFF);
            this.thread_worker = new Thread(thread_worker_func);
            this.thread_worker_signal = new ManualResetEventSlim(false);
            this.isControllerInitialized = false;
            this.gui_dispatcher_queue = new Queue<Action>();
        }

        private void btn_connect_Click(object sender, EventArgs e)
        {
            btn_connect.Enabled = false;
            btn_reset.Enabled = true;
            timer_gui_dispatcher.Enabled = true;

            this.thread_worker.Start(this);
        }

        private void Form1_FormClosing(object sender, FormClosingEventArgs e)
        {
            this.thread_worker_signal.Set();
            this.thread_worker.Join(2000);
        }

        private void timer_gui_dispatcher_Tick(object sender, EventArgs e)
        {
            while (this.gui_dispatcher_queue.Count > 0)
            {
                this.gui_dispatcher_queue.Dequeue()();
            }
        }
    }
}
