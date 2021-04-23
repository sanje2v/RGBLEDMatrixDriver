using System;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;

namespace ElevatedInformationProviderService
{
    class ServiceSecurity : NativeObjectSecurity
    {
        private SafeHandle serviceHandle;

        public ServiceSecurity(SafeHandle serviceHandle)
            : base(false, ResourceType.Service, serviceHandle, AccessControlSections.Access)
              => this.serviceHandle = serviceHandle;

        public override Type AccessRightType
        {
            get { return typeof(ServiceAccessRights); }
        }

        public override Type AccessRuleType
        {
            get { return typeof(ServiceAccessRule); }
        }

        public void Persist()
        {
            this.Persist(this.serviceHandle, AccessControlSections.Access);
        }

        public override Type AuditRuleType => throw new NotImplementedException();

        public override AccessRule AccessRuleFactory(IdentityReference identityReference,
                                                     int accessMask,
                                                     bool isInherited,
                                                     InheritanceFlags inheritanceFlags,
                                                     PropagationFlags propagationFlags,
                                                     AccessControlType type) => throw new NotImplementedException();

        public override AuditRule AuditRuleFactory(IdentityReference identityReference,
                                                   int accessMask,
                                                   bool isInherited,
                                                   InheritanceFlags inheritanceFlags,
                                                   PropagationFlags propagationFlags,
                                                   AuditFlags flags) => throw new NotImplementedException();
    }

    public class ServiceAccessRule : AccessRule<ServiceAccessRights>
    {
        public ServiceAccessRule(IdentityReference identityReference,
                                 ServiceAccessRights accessMask,
                                 AccessControlType type)
            : base(identityReference, accessMask, InheritanceFlags.None, PropagationFlags.None, type) {}
    }

    [Flags]
    public enum ServiceAccessRights
    {
        // REF: https://docs.microsoft.com/en-us/windows/win32/services/service-security-and-access-rights
        AllAccess = 0xF01FF,
        ChangeConfig = 0x0002,
        EnumerateDependents = 0x0008,
        Interrogate = 0x0080,
        PauseContinue = 0x0040,
        QueryConfig = 0x0001,
        QueryStatus = 0x0004,
        Start = 0x0010,
        Stop = 0x0020,
        UserDefinedControl = 0x0100,

        AccessSystemSecurity = 0x01000000,
        Delete = 0x10000,
        ReadControl = 0x20000,
        WriteDAC = 0x40000,
        WriteOwner = 0x80000,

        // STANDARD_RIGHTS_READ = STANDARD_RIGHTS_WRITE = STANDARD_RIGHTS_EXECUTE = 0x00020000
        GenericRead = 0x00020000 | QueryConfig | QueryStatus | Interrogate | EnumerateDependents,
        GenericWrite = 0x00020000 | ChangeConfig,
        GenericExecute = 0x00020000 | Start | Stop | PauseContinue | UserDefinedControl
    }
}