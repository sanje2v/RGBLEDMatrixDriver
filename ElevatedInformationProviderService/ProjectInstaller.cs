using System.Security.AccessControl;
using System.ComponentModel;
using System.Configuration.Install;
using System.Security.Principal;

namespace ElevatedInformationProviderService
{
    [RunInstaller(true)]
    public partial class ProjectInstaller : System.Configuration.Install.Installer
    {
        public ProjectInstaller()
        {
            InitializeComponent();
        }

        private void serviceInstaller_AfterInstall(object sender, InstallEventArgs e)
        {
            /* REFERENCES:
             * 1. https://stackoverflow.com/questions/11637764/how-do-i-set-acl-for-a-windows-service-in-net
             * 2. https://stackoverflow.com/questions/15771998/how-to-give-a-user-permission-to-start-and-stop-a-particular-service-using-c-sha
             * 3. https://stackoverflow.com/questions/1909084/is-there-a-way-to-modify-a-process-dacl-in-c-sharp
            */

            // Allow this service to be started/stopped/pause/user defined control by any authenticated user (i.e. funcs/cpugpu_usage.py)
            var serviceSecurity = new ServiceSecurity(serviceController.ServiceHandle);
            var rule = new ServiceAccessRule(new SecurityIdentifier(WellKnownSidType.AuthenticatedUserSid, null),
                                                                    ServiceAccessRights.GenericExecute, AccessControlType.Allow);
            serviceSecurity.ModifyAccessRule(AccessControlModification.Reset, rule, out bool _);
            serviceSecurity.Persist();  // CAUTION: Don't forget to commit the changed access rule
        }
    }
}