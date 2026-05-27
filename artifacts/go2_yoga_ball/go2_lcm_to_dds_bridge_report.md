# Go2 LCM To DDS Bridge Report

- Status: PASS
- Unitree SDK2 Python commit: `794fb2b3fd9165fd245a7b568698d9e97d8ac0a0`
- Claim: LCM remains an internal DrEureka policy contract. The Go2 deploy bridge owns the conversion to Unitree SDK2 DDS.
- Command order: DrEureka publishes `pd_plustau_targets` in Unitree motor order because `LCMAgent` applies `StateEstimator.joint_idxs` before publishing.
- Missing required bridge tokens: `[]`

### Lcm Policy Command Fields

- Source: `thirdparties/DrEureka/globe_walking/go1_gym_deploy/lcm_types/pd_tau_targets_lcmt.lcm:1`

```text
struct pd_tau_targets_lcmt
{
    double q_des[12];
    double qd_des[12];
    double tau_ff[12];
    double kp[12];
    double kd[12];
    int64_t timestamp_us;
    int64_t id;
    int64_t robot_id;
```

### Lcm Policy Publisher

- Source: `thirdparties/DrEureka/globe_walking/go1_gym_deploy/envs/lcm_agent.py:194`

```text
    def publish_action(self, action, hard_reset=False):

        command_for_robot = pd_tau_targets_lcmt()
        self.joint_pos_target = \
            (action[0, :12].detach().cpu().numpy() * self.cfg["control"]["action_scale"]).flatten()
        self.joint_pos_target[[0, 3, 6, 9]] *= self.cfg["control"]["hip_scale_reduction"]
        # self.joint_pos_target[[0, 3, 6, 9]] *= -1
        self.joint_pos_target = self.joint_pos_target
        self.joint_pos_target += self.default_dof_pos
        joint_pos_target = self.joint_pos_target[self.joint_idxs]
        self.joint_vel_target = np.zeros(12)
        # print(f'cjp {self.joint_pos_target}')

        command_for_robot.q_des = joint_pos_target
        command_for_robot.qd_des = self.joint_vel_target
        command_for_robot.kp = self.p_gains
        command_for_robot.kd = self.d_gains
        command_for_robot.tau_ff = np.zeros(12)
        command_for_robot.se_contactState = np.zeros(4)
        command_for_robot.timestamp_us = int(time.time() * 10 ** 6)
        command_for_robot.id = 0

        if hard_reset:
            command_for_robot.id = -1


        self.torques = (self.joint_pos_target - self.dof_pos) * self.p_gains + (self.joint_vel_target - self.dof_vel) * self.d_gains

        lc.publish("pd_plustau_targets", command_for_robot.encode())
```

### Dr Eureka State Reorder

- Source: `thirdparties/DrEureka/globe_walking/go1_gym_deploy/utils/cheetah_state_estimator.py:51`

```text
class StateEstimator:
    def __init__(self, lc, use_cameras=True):

        # reverse legs
        self.joint_idxs = [3, 4, 5, 0, 1, 2, 9, 10, 11, 6, 7, 8]
        self.contact_idxs = [1, 0, 3, 2]
```

### Lcm State Subscriptions

- Source: `thirdparties/DrEureka/globe_walking/go1_gym_deploy/utils/cheetah_state_estimator.py:111`

```text
        self.imu_subscription = self.lc.subscribe("state_estimator_data", self._imu_cb)
        self.legdata_state_subscription = self.lc.subscribe("leg_control_data", self._legdata_cb)
        self.rc_command_subscription = self.lc.subscribe("rc_command", self._rc_command_cb)
```

### Lcm Leg State Fields

- Source: `thirdparties/DrEureka/globe_walking/go1_gym_deploy/lcm_types/leg_control_data_lcmt.lcm:1`

```text
struct leg_control_data_lcmt 
{
    float q[12];
    float qd[12];
    float p[12];
    float v[12];
    float tau_est[12];
    int64_t timestamp_us;
    int64_t id;
```

### Lcm Imu State Fields

- Source: `thirdparties/DrEureka/globe_walking/go1_gym_deploy/lcm_types/state_estimator_lcmt.lcm:1`

```text
struct state_estimator_lcmt
{
    float p[3];
    float vWorld[3];
    float vBody[3];
    float rpy[3];
    float omegaBody[3];
    float omegaWorld[3];
    float quat[4];
    float contact_estimate[4];
    float aBody[3];
    float aWorld[3];
    int64_t timestamp_us;
    int64_t id;
    int64_t robot_id;
}
```

### Dds Channel Factory

- Source: `thirdparties/unitree_sdk2_python/unitree_sdk2py/core/channel.py:256`

```text
class ChannelPublisher:
    def __init__(self, name: str, type: Any):
        factory = ChannelFactory()
        self.__channel = factory.CreateChannel(name, type)
        self.__inited = False

    def Init(self):
        if not self.__inited:
            self.__channel.SetWriter(None)
            self.__inited = True

    def Close(self):
        self.__channel.CloseWriter()
        self.__inited = False

    def Write(self, sample: Any, timeout: float = None):
        return self.__channel.Write(sample, timeout)

"""
" class ChannelSubscriber
"""
class ChannelSubscriber:
    def __init__(self, name: str, type: Any):
        factory = ChannelFactory()
        self.__channel = factory.CreateChannel(name, type)
        self.__inited = False

    def Init(self, handler: Callable = None, queueLen: int = 0):
        if not self.__inited:
            self.__channel.SetReader(None, handler, queueLen)
            self.__inited = True

    def Close(self):
        self.__channel.CloseReader()
        self.__inited = False

    def Read(self, timeout: int = None):
        return self.__channel.Read(timeout)

"""
" function ChannelFactoryInitialize. used to intialize channel everenment.
"""
def ChannelFactoryInitialize(id: int = 0, networkInterface: str = None):
    factory = ChannelFactory()
    if not factory.Init(id, networkInterface):
        raise Exception("channel factory init error.")
```

### Dds Lowcmd Default

- Source: `thirdparties/unitree_sdk2_python/unitree_sdk2py/idl/default.py:147`

```text
def unitree_go_msg_dds__MotorCmd_():
    return MotorCmd_(0, 0.0, 0.0, 0.0, 0.0, 0.0, [0, 0, 0])

def unitree_go_msg_dds__MotorState_():
    return MotorState_(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, [0, 0])

def unitree_go_msg_dds__LowCmd_():
    return LowCmd_([0, 0], 0, 0, [0, 0], [0, 0], 0, [unitree_go_msg_dds__MotorCmd_() for i in range(20)],
                unitree_go_msg_dds__BmsCmd_(),
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0], 0, 0, 0)
```

### Dds Lowcmd Crc Fields

- Source: `thirdparties/unitree_sdk2_python/unitree_sdk2py/utils/crc.py:51`

```text
    def __PackLowCmd(self, cmd: LowCmd_):
        origData = []
        origData.extend(cmd.head)
        origData.append(cmd.level_flag)
        origData.append(cmd.frame_reserve)
        origData.extend(cmd.sn)
        origData.extend(cmd.version)
        origData.append(cmd.bandwidth)

        for i in range(20):
            origData.append(cmd.motor_cmd[i].mode)
            origData.append(cmd.motor_cmd[i].q)
            origData.append(cmd.motor_cmd[i].dq)
            origData.append(cmd.motor_cmd[i].tau)
            origData.append(cmd.motor_cmd[i].kp)
            origData.append(cmd.motor_cmd[i].kd)
            origData.extend(cmd.motor_cmd[i].reserve)

        origData.append(cmd.bms_cmd.off)
        origData.extend(cmd.bms_cmd.reserve)

        origData.extend(cmd.wireless_remote)
        origData.extend(cmd.led)
        origData.extend(cmd.fan)
        origData.append(cmd.gpio)
        origData.append(cmd.reserve)
        origData.append(cmd.crc)

        return self.__Trans(struct.pack(self.__packFmtLowCmd, *origData))
```

### Bridge Imports

- Source: `scripts/go2_yoga_ball/lcm_to_dds_bridge.py:21`

```text
if str(DREUREKA / "globe_walking" / "go1_gym_deploy") not in sys.path:
    sys.path.insert(0, str(DREUREKA / "globe_walking" / "go1_gym_deploy"))

from go1_gym_deploy.lcm_types.leg_control_data_lcmt import leg_control_data_lcmt  # noqa: E402
from go1_gym_deploy.lcm_types.pd_tau_targets_lcmt import pd_tau_targets_lcmt  # noqa: E402
from go1_gym_deploy.lcm_types.rc_command_lcmt import rc_command_lcmt  # noqa: E402
from go1_gym_deploy.lcm_types.state_estimator_lcmt import state_estimator_lcmt  # noqa: E402
from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher, ChannelSubscriber  # noqa: E402
from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowCmd_  # noqa: E402
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowCmd_, LowState_  # noqa: E402
from unitree_sdk2py.utils.crc import CRC  # noqa: E402
```

### Bridge Dds Initialization

- Source: `scripts/go2_yoga_ball/lcm_to_dds_bridge.py:61`

```text
        self.lc = lcm.LCM(lcm_url)
        self.crc = CRC()
        self.low_cmd = unitree_go_msg_dds__LowCmd_()
        self.lowcmd_pub = ChannelPublisher("rt/lowcmd", LowCmd_)
        self.lowcmd_pub.Init()
        self.lowstate_sub = ChannelSubscriber("rt/lowstate", LowState_)
        self.lowstate_sub.Init(self.on_lowstate, 10)
        self.lc.subscribe("pd_plustau_targets", self.on_lcm_command)
        self.last_lowstate: Any | None = None
        self.last_lowstate_monotonic: float | None = None
        self.last_cmd_monotonic: float | None = None
        self.init_lowcmd()
```

### Bridge Lowcmd Defaults

- Source: `scripts/go2_yoga_ball/lcm_to_dds_bridge.py:80`

```text
            motor = self.low_cmd.motor_cmd[i]
            motor.mode = 0x01
            motor.q = 2.146e9
            motor.dq = 16000.0
            motor.kp = 0.0
            motor.kd = 0.0
            motor.tau = 0.0

    def on_lcm_command(self, channel: str, data: bytes) -> None:
        del channel
        msg = pd_tau_targets_lcmt.decode(data)
        for i in range(12):
            motor = self.low_cmd.motor_cmd[i]
```

### Bridge Lcm To Dds Command Mapping

- Source: `scripts/go2_yoga_ball/lcm_to_dds_bridge.py:94`

```text
            motor.q = float(msg.q_des[i])
            motor.dq = float(msg.qd_des[i])
            motor.tau = float(msg.tau_ff[i])
            motor.kp = float(msg.kp[i])
            motor.kd = float(msg.kd[i])
        self.low_cmd.crc = self.crc.Crc(self.low_cmd)
        self.lowcmd_pub.Write(self.low_cmd)
        self.last_cmd_monotonic = time.monotonic()

    def on_lowstate(self, msg: LowState_) -> None:
        self.last_lowstate = msg
        self.last_lowstate_monotonic = time.monotonic()
        self.publish_lcm_state(msg)

    def publish_lcm_state(self, msg: LowState_) -> None:
        now_us = int(time.time() * 1e6)
```

### Bridge Dds To Lcm State Mapping

- Source: `scripts/go2_yoga_ball/lcm_to_dds_bridge.py:115`

```text
        leg.tau_est = [float(msg.motor_state[i].tau_est) for i in range(12)]
        leg.timestamp_us = now_us
        leg.id = 0
        leg.robot_id = 1
        self.lc.publish("leg_control_data", leg.encode())

        state = state_estimator_lcmt()
        state.p = [0.0, 0.0, 0.0]
        state.vWorld = [0.0, 0.0, 0.0]
        state.vBody = [0.0, 0.0, 0.0]
        state.quat = [float(v) for v in msg.imu_state.quaternion]
        state.rpy = [float(v) for v in msg.imu_state.rpy]
        if state.rpy == [0.0, 0.0, 0.0] and state.quat != [0.0, 0.0, 0.0, 0.0]:
            state.rpy = quat_to_rpy(state.quat)
        state.omegaBody = [float(v) for v in msg.imu_state.gyroscope]
        state.omegaWorld = list(state.omegaBody)
        state.aBody = [float(v) for v in msg.imu_state.accelerometer]
        state.aWorld = list(state.aBody)
        state.contact_estimate = [float(v) for v in msg.foot_force_est]
        if not any(state.contact_estimate):
            state.contact_estimate = [float(v) for v in msg.foot_force]
        state.timestamp_us = now_us
        state.id = 0
        state.robot_id = 1
        self.lc.publish("state_estimator_data", state.encode())

        rc = rc_command_lcmt()
        rc.mode = 0
        rc.left_stick = [0.0, 0.0]
        rc.right_stick = [0.0, 0.0]
        rc.knobs = [0.0, 0.0]
        rc.left_upper_switch = 0
        rc.left_lower_left_switch = 0
        rc.left_lower_right_switch = 0
        rc.right_upper_switch = 0
        rc.right_lower_left_switch = 0
        rc.right_lower_right_switch = 0
        self.lc.publish("rc_command", rc.encode())

    def spin(self, duration_s: float | None) -> int:
        start = time.monotonic()
        while duration_s is None or time.monotonic() - start < duration_s:
            readable, _, _ = select.select([self.lc.fileno()], [], [], 0.001)
            if readable:
                self.lc.handle()
```

### Bridge Spin Lcm Poll

- Source: `scripts/go2_yoga_ball/lcm_to_dds_bridge.py:176`

```text
    return bridge.spin(args.duration_s)


if __name__ == "__main__":
    raise SystemExit(main())
```
