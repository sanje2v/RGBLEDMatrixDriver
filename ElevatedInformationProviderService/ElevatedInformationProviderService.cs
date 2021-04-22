using System;
using System.IO;
using System.IO.Pipes;
using System.Linq;
using System.ServiceProcess;
using OpenHardwareMonitor.Hardware;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Threading;
using System.Threading.Tasks;
using System.Text;
using System.Diagnostics;

namespace ElevatedInformationProviderService
{
    public partial class ElevatedInformationProviderService : ServiceBase
    {
        private static readonly int INPUT_BUFFER_SIZE = 32;
        private static readonly int OUTPUT_BUFFER_SIZE = sizeof(float);

        private Computer _computer;
        private IHardware _CPU_hardware;
        private ISensor _CPU_package_temp_sensor;
        private CancellationTokenSource _pipe_cancellation_tokensource;
        private NamedPipeServerStream _pipe_server;
        private Task _communicate_with_client;

        public ElevatedInformationProviderService()
        {
            InitializeComponent();
        }

        protected override async void OnStart(string[] args)
        {
            // Initialize 'OpenHardwareMonitor' to query CPU temperatures
            this._computer = new Computer { CPUEnabled = true };
            this._computer.Open();
            this._computer.Accept(new UpdateVisitor());
            this._CPU_hardware = this._computer.Hardware.SingleOrDefault(h => h.HardwareType == HardwareType.CPU);
            this._CPU_package_temp_sensor = this._CPU_hardware.Sensors.SingleOrDefault(s => s.SensorType == SensorType.Temperature &&
                                                                                       s.Name == "CPU Package");
            this._pipe_server = CreatePipeServer();
            this._pipe_cancellation_tokensource = new CancellationTokenSource();

            try
            {
                while (true)
                {
                    this._communicate_with_client = this.CommunicateWithClient(this._pipe_cancellation_tokensource.Token);
                    await this._communicate_with_client;
                }
            }
            catch (OperationCanceledException) {}
        }

        private NamedPipeServerStream CreatePipeServer()
        {
            return new NamedPipeServerStream(@"\\.\ElevatedInformationProviderService",
                                             PipeDirection.InOut,
                                             maxNumberOfServerInstances: 1,
                                             PipeTransmissionMode.Byte,
                                             PipeOptions.Asynchronous,
                                             INPUT_BUFFER_SIZE,
                                             OUTPUT_BUFFER_SIZE,    // Size of float
                                             this.CreatePipeSecurity(),
                                             HandleInheritability.Inheritable);
        }

        private async Task CommunicateWithClient(CancellationToken cancellationToken)
        {
            try
            {
                await this._pipe_server.WaitForConnectionAsync(cancellationToken);

                var readBuffer = new byte[INPUT_BUFFER_SIZE];
                while (this._pipe_server.IsConnected)
                {
                    var bytesRead = await this._pipe_server.ReadAsync(readBuffer, 0, readBuffer.Length, cancellationToken);
                    if (bytesRead > 0 && Encoding.UTF8.GetString(readBuffer) == "GetCPUPackageTemp")
                    {
                        var writeBuffer = BitConverter.GetBytes(GetCPUPackageTemp());
                        Debug.Assert(writeBuffer.Length == sizeof(float));
                        await this._pipe_server.WriteAsync(writeBuffer, 0, writeBuffer.Length, cancellationToken);
                    }
                }
            }
            catch (IOException)
            {
                // Client disconnected on its end so we need to disconnect on server's end as well
                this._pipe_server.Disconnect();
            }
        }

        private void ClosePipeServer()
        {
            if (this._pipe_cancellation_tokensource.Token.CanBeCanceled)
                this._pipe_cancellation_tokensource.Cancel();

            while (this._communicate_with_client.Status != TaskStatus.Canceled);
            this._pipe_server.Close();
            this._pipe_server.Dispose();
            this._pipe_cancellation_tokensource.Dispose();
        }

        private PipeSecurity CreatePipeSecurity()
        {
            // Allow Everyone read access to the pipe
            var pipeSecurity = new PipeSecurity();
            pipeSecurity.SetAccessRule(new PipeAccessRule(new SecurityIdentifier(WellKnownSidType.AuthenticatedUserSid, null),
                                       PipeAccessRights.ReadWrite, AccessControlType.Allow));

            return pipeSecurity;
        }

        public float GetCPUPackageTemp()
        {
            float temperature = 0.0f;

            if (this._CPU_hardware != null)
            {
                this._CPU_hardware.Update();

                if (this._CPU_package_temp_sensor != null)
                    temperature = this._CPU_package_temp_sensor.Value.GetValueOrDefault(0.0f);
            }

            return temperature;
        }

        protected override void OnStop()
        {
            ClosePipeServer();

            if (this._computer != null)
                this._computer.Close();
        }
    }
}