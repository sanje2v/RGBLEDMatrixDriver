using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Diagnostics;
using System.Linq;
using System.ServiceProcess;
using System.Text;
using System.Threading.Tasks;

namespace RGBLEDMatrixDriverService
{
    public partial class ControllerService : ServiceBase
    {
        public ControllerService()
        {
            InitializeComponent();

            // Setup event logger
            var eventLog = new System.Diagnostics.EventLog();
            if (!System.Diagnostics.EventLog.SourceExists("RGBLEDMatrixDriverServiceSource"))
            {
                System.Diagnostics.EventLog.CreateEventSource(
                    "RGBLEDMatrixDriverServiceSource", "EventsLog");
            }
            eventLog.Source = "RGBLEDMatrixDriverServiceSource";
            eventLog.Log = "EventsLog";
        }

        protected override void OnStart(string[] args)
        {
        }

        protected override void OnStop()
        {
        }
    }
}
