namespace WindowsFormsApp1
{
    partial class Form1
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();
            this.txt_serialoutput = new System.Windows.Forms.TextBox();
            this.lbl_status = new System.Windows.Forms.Label();
            this.btn_connect = new System.Windows.Forms.Button();
            this.btn_reset = new System.Windows.Forms.Button();
            this.timer_gui_dispatcher = new System.Windows.Forms.Timer(this.components);
            this.SuspendLayout();
            // 
            // txt_serialoutput
            // 
            this.txt_serialoutput.Location = new System.Drawing.Point(13, 13);
            this.txt_serialoutput.Multiline = true;
            this.txt_serialoutput.Name = "txt_serialoutput";
            this.txt_serialoutput.ReadOnly = true;
            this.txt_serialoutput.ScrollBars = System.Windows.Forms.ScrollBars.Both;
            this.txt_serialoutput.Size = new System.Drawing.Size(523, 348);
            this.txt_serialoutput.TabIndex = 0;
            this.txt_serialoutput.WordWrap = false;
            // 
            // lbl_status
            // 
            this.lbl_status.AutoSize = true;
            this.lbl_status.Location = new System.Drawing.Point(13, 368);
            this.lbl_status.Name = "lbl_status";
            this.lbl_status.Size = new System.Drawing.Size(0, 13);
            this.lbl_status.TabIndex = 1;
            // 
            // btn_connect
            // 
            this.btn_connect.Location = new System.Drawing.Point(551, 11);
            this.btn_connect.Name = "btn_connect";
            this.btn_connect.Size = new System.Drawing.Size(88, 23);
            this.btn_connect.TabIndex = 2;
            this.btn_connect.Text = "Connect";
            this.btn_connect.UseVisualStyleBackColor = true;
            this.btn_connect.Click += new System.EventHandler(this.btn_connect_Click);
            // 
            // btn_reset
            // 
            this.btn_reset.Enabled = false;
            this.btn_reset.Location = new System.Drawing.Point(551, 40);
            this.btn_reset.Name = "btn_reset";
            this.btn_reset.Size = new System.Drawing.Size(88, 23);
            this.btn_reset.TabIndex = 3;
            this.btn_reset.Text = "Send reset";
            this.btn_reset.UseVisualStyleBackColor = true;
            // 
            // timer_gui_dispatcher
            // 
            this.timer_gui_dispatcher.Interval = 200;
            this.timer_gui_dispatcher.Tick += new System.EventHandler(this.timer_gui_dispatcher_Tick);
            // 
            // Form1
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(652, 400);
            this.Controls.Add(this.btn_reset);
            this.Controls.Add(this.btn_connect);
            this.Controls.Add(this.lbl_status);
            this.Controls.Add(this.txt_serialoutput);
            this.Name = "Form1";
            this.Text = "Form1";
            this.FormClosing += new System.Windows.Forms.FormClosingEventHandler(this.Form1_FormClosing);
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.TextBox txt_serialoutput;
        private System.Windows.Forms.Label lbl_status;
        private System.Windows.Forms.Button btn_connect;
        private System.Windows.Forms.Button btn_reset;
        private System.Windows.Forms.Timer timer_gui_dispatcher;
    }
}

