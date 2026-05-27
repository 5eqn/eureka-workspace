# Go2 MuJoCo DDS Endpoint Report

- Status: PASS
- Unitree MuJoCo commit: `c598f103acb87a5fd3de7c9037f4dab6aa7f232b`
- Claim: Unitree MuJoCo Go2 is the source-of-truth DDS robot endpoint. It consumes `rt/lowcmd`, publishes `rt/lowstate`, and applies the SDK2 `LowCmd` actuator equation.
- Real-swap target: replace the simulator container with a real Go2 backend on the selected network interface; keep policy/deploy code unchanged except backend/network selection and safety procedure.
- LCM mentions in endpoint sources: `[]`

### Upstream Real Swap Claim

- Source: `thirdparties/unitree_mujoco/readme.md:3`

```text
`unitree_mujoco` is a simulator developed based on `Unitree sdk2` and `mujoco`. Users can easily integrate the control programs developed with `Unitree_sdk2`, `unitree_ros2`, and `unitree_sdk2_python` into this simulator, enabling a seamless transition from simulation to physical development. The repository includes two versions of the simulator implemented in C++ and Python, with a structure as follows:
![](./doc/func.png)

## Directory Structure
- `simulate`: Simulator implemented based on unitree_sdk2 and mujoco (C++, recommended)
- `simulate_python`: Simulator implemented based on unitree_sdk2_python and mujoco (Python)
- `unitree_robots`: MJCF description files for robots supported by unitree_sdk2
```

### Real Robot Interface Argument

- Source: `thirdparties/unitree_mujoco/readme.md:253`

```text
```
2. Run:
```bash
./stand_go2 # Control the robot in the simulation (make sure the Go2 simulation scene has been loaded)
./stand_go2 enp3s0 # Control the physical robot, where enp3s0 is the name of the network card connected to the robot
```
```

### Dds Topic Setup

- Source: `thirdparties/unitree_mujoco/simulate/src/unitree_sdk2_bridge.h:151`

```text
template <typename LowCmd_t, typename LowState_t>
class RobotBridge : public UnitreeSDK2BridgeBase
{
using HighState_t = unitree::robot::go2::publisher::SportModeState;
using WirelessController_t = unitree::robot::go2::publisher::WirelessController;

public:
    RobotBridge(mjModel *model, mjData *data) : UnitreeSDK2BridgeBase(model, data)
    {
        lowcmd = std::make_shared<LowCmd_t>("rt/lowcmd");
        lowstate = std::make_unique<LowState_t>();
        lowstate->joystick = joystick;
        highstate = std::make_unique<HighState_t>();
        wireless_controller = std::make_unique<WirelessController_t>();
        wireless_controller->joystick = joystick;
```

### Lowcmd Torque Equation

- Source: `thirdparties/unitree_mujoco/simulate/src/unitree_sdk2_bridge.h:178`

```text
        // lowcmd
        {
            std::lock_guard<std::mutex> lock(lowcmd->mutex_);
            for(int i(0); i<num_motor_; i++) {
                auto & m = lowcmd->msg_.motor_cmd()[i];
                mj_data_->ctrl[i] = m.tau() +
                                    m.kp() * (m.q() - mj_data_->sensordata[i]) +
                                    m.kd() * (m.dq() - mj_data_->sensordata[i + num_motor_]);
            }
```

### Lowstate Motor State

- Source: `thirdparties/unitree_mujoco/simulate/src/unitree_sdk2_bridge.h:189`

```text
        // lowstate
        if(lowstate->trylock()) {
            for(int i(0); i<num_motor_; i++) {
                lowstate->msg_.motor_state()[i].q() = mj_data_->sensordata[i];
                lowstate->msg_.motor_state()[i].dq() = mj_data_->sensordata[i + num_motor_];
                lowstate->msg_.motor_state()[i].tau_est() = mj_data_->sensordata[i + 2 * num_motor_];
            }
```

### Lowstate Imu

- Source: `thirdparties/unitree_mujoco/simulate/src/unitree_sdk2_bridge.h:197`

```text
            if(imu_quat_adr_ >= 0) {
                lowstate->msg_.imu_state().quaternion()[0] = mj_data_->sensordata[imu_quat_adr_ + 0];
                lowstate->msg_.imu_state().quaternion()[1] = mj_data_->sensordata[imu_quat_adr_ + 1];
                lowstate->msg_.imu_state().quaternion()[2] = mj_data_->sensordata[imu_quat_adr_ + 2];
                lowstate->msg_.imu_state().quaternion()[3] = mj_data_->sensordata[imu_quat_adr_ + 3];

                double w = lowstate->msg_.imu_state().quaternion()[0];
                double x = lowstate->msg_.imu_state().quaternion()[1];
                double y = lowstate->msg_.imu_state().quaternion()[2];
                double z = lowstate->msg_.imu_state().quaternion()[3];

                lowstate->msg_.imu_state().rpy()[0] = atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y));
                lowstate->msg_.imu_state().rpy()[1] = asin(2 * (w * y - z * x));
                lowstate->msg_.imu_state().rpy()[2] = atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z));
            }
            
            if(imu_gyro_adr_ >= 0) {
                lowstate->msg_.imu_state().gyroscope()[0] = mj_data_->sensordata[imu_gyro_adr_ + 0];
                lowstate->msg_.imu_state().gyroscope()[1] = mj_data_->sensordata[imu_gyro_adr_ + 1];
                lowstate->msg_.imu_state().gyroscope()[2] = mj_data_->sensordata[imu_gyro_adr_ + 2];
            }

            if(imu_acc_adr_ >= 0) {
                lowstate->msg_.imu_state().accelerometer()[0] = mj_data_->sensordata[imu_acc_adr_ + 0];
                lowstate->msg_.imu_state().accelerometer()[1] = mj_data_->sensordata[imu_acc_adr_ + 1];
                lowstate->msg_.imu_state().accelerometer()[2] = mj_data_->sensordata[imu_acc_adr_ + 2];
            }
            
            lowstate->msg_.tick() = std::round(mj_data_->time / 1e-3);
            lowstate->unlockAndPublish();
```

### Go2 Bridge Type

- Source: `thirdparties/unitree_mujoco/simulate/src/unitree_sdk2_bridge.h:257`

```text
using Go2Bridge = RobotBridge<unitree::robot::go2::subscription::LowCmd, unitree::robot::go2::publisher::LowState>;
```

### Dds Factory And Go2 Selection

- Source: `thirdparties/unitree_mujoco/simulate/src/main.cc:587`

```text
  unitree::robot::ChannelFactory::Instance()->Init(param::config.domain_id, param::config.interface);


  int body_id = mj_name2id(m, mjOBJ_BODY, "torso_link");
  if (body_id < 0) {
    body_id = mj_name2id(m, mjOBJ_BODY, "base_link");
  }
  param::config.band_attached_link = 6 * body_id;
  
  std::unique_ptr<UnitreeSDK2BridgeBase> interface = nullptr;
  if (m->nu > NUM_MOTOR_IDL_GO) {
    interface = std::make_unique<G1Bridge>(m, d);
  } else {
    interface = std::make_unique<Go2Bridge>(m, d);
  }
  interface->start();
```

### Go2 Joint And Actuator Limits

- Source: `thirdparties/unitree_mujoco/unitree_robots/go2/go2.xml:7`

```text
    <default class="go2">
      <geom friction="0.4" margin="0.001" condim="1"/>
      <joint axis="0 1 0" damping="0.1" armature="0.01" frictionloss="0.2"/>
      <motor ctrlrange="-23.7 23.7"/>
      <default class="abduction">
        <joint axis="1 0 0" range="-1.0472 1.0472"/>
      </default>
      <default class="hip">
        <default class="front_hip">
          <joint range="-1.5708 3.4907"/>
        </default>
        <default class="back_hip">
          <joint range="-0.5236 4.5379"/>
        </default>
      </default>
      <default class="knee">
        <joint range="-2.7227 -0.83776"/>
        <motor ctrlrange="-45.43 45.43"/>
```

### Go2 Motor Order

- Source: `thirdparties/unitree_mujoco/unitree_robots/go2/go2.xml:222`

```text
  <actuator>
    <motor class="abduction" name="FR_hip" joint="FR_hip_joint" />
    <motor class="hip" name="FR_thigh" joint="FR_thigh_joint" />
    <motor class="knee" name="FR_calf" joint="FR_calf_joint" />
    <motor class="abduction" name="FL_hip" joint="FL_hip_joint" />
    <motor class="hip" name="FL_thigh" joint="FL_thigh_joint" />
    <motor class="knee" name="FL_calf" joint="FL_calf_joint" />
    <motor class="abduction" name="RR_hip" joint="RR_hip_joint" />
    <motor class="hip" name="RR_thigh" joint="RR_thigh_joint" />
    <motor class="knee" name="RR_calf" joint="RR_calf_joint" />
    <motor class="abduction" name="RL_hip" joint="RL_hip_joint" />
    <motor class="hip" name="RL_thigh" joint="RL_thigh_joint" />
    <motor class="knee" name="RL_calf" joint="RL_calf_joint" />
```

### Go2 Sensor Order

- Source: `thirdparties/unitree_mujoco/unitree_robots/go2/go2.xml:238`

```text
    <jointpos name="FR_hip_pos" joint="FR_hip_joint" />
    <jointpos name="FR_thigh_pos" joint="FR_thigh_joint" />
    <jointpos name="FR_calf_pos" joint="FR_calf_joint" />
    <jointpos name="FL_hip_pos" joint="FL_hip_joint" />
    <jointpos name="FL_thigh_pos" joint="FL_thigh_joint" />
    <jointpos name="FL_calf_pos" joint="FL_calf_joint" />
    <jointpos name="RR_hip_pos" joint="RR_hip_joint" />
    <jointpos name="RR_thigh_pos" joint="RR_thigh_joint" />
    <jointpos name="RR_calf_pos" joint="RR_calf_joint" />
    <jointpos name="RL_hip_pos" joint="RL_hip_joint" />
    <jointpos name="RL_thigh_pos" joint="RL_thigh_joint" />
    <jointpos name="RL_calf_pos" joint="RL_calf_joint" />

    <jointvel name="FR_hip_vel" joint="FR_hip_joint" />
    <jointvel name="FR_thigh_vel" joint="FR_thigh_joint" />
    <jointvel name="FR_calf_vel" joint="FR_calf_joint" />
    <jointvel name="FL_hip_vel" joint="FL_hip_joint" />
    <jointvel name="FL_thigh_vel" joint="FL_thigh_joint" />
    <jointvel name="FL_calf_vel" joint="FL_calf_joint" />
    <jointvel name="RR_hip_vel" joint="RR_hip_joint" />
    <jointvel name="RR_thigh_vel" joint="RR_thigh_joint" />
    <jointvel name="RR_calf_vel" joint="RR_calf_joint" />
    <jointvel name="RL_hip_vel" joint="RL_hip_joint" />
    <jointvel name="RL_thigh_vel" joint="RL_thigh_joint" />
    <jointvel name="RL_calf_vel" joint="RL_calf_joint" />

    <jointactuatorfrc name="FR_hip_torque" joint="FR_hip_joint" noise="0.01" />
    <jointactuatorfrc name="FR_thigh_torque" joint="FR_thigh_joint" noise="0.01" />
    <jointactuatorfrc name="FR_calf_torque" joint="FR_calf_joint" noise="0.01" />
    <jointactuatorfrc name="FL_hip_torque" joint="FL_hip_joint" noise="0.01" />
    <jointactuatorfrc name="FL_thigh_torque" joint="FL_thigh_joint" noise="0.01" />
    <jointactuatorfrc name="FL_calf_torque" joint="FL_calf_joint" noise="0.01" />
    <jointactuatorfrc name="RR_hip_torque" joint="RR_hip_joint" noise="0.01" />
    <jointactuatorfrc name="RR_thigh_torque" joint="RR_thigh_joint" noise="0.01" />
    <jointactuatorfrc name="RR_calf_torque" joint="RR_calf_joint" noise="0.01" />
    <jointactuatorfrc name="RL_hip_torque" joint="RL_hip_joint" noise="0.01" />
    <jointactuatorfrc name="RL_thigh_torque" joint="RL_thigh_joint" noise="0.01" />
    <jointactuatorfrc name="RL_calf_torque" joint="RL_calf_joint" noise="0.01" />
```

### Python Dds Topics

- Source: `thirdparties/unitree_mujoco/simulate_python/unitree_sdk2py_bridge.py:25`

```text
TOPIC_LOWCMD = "rt/lowcmd"
TOPIC_LOWSTATE = "rt/lowstate"
TOPIC_HIGHSTATE = "rt/sportmodestate"
TOPIC_WIRELESS_CONTROLLER = "rt/wirelesscontroller"

```

### Python Lowcmd Torque Equation

- Source: `thirdparties/unitree_mujoco/simulate_python/unitree_sdk2py_bridge.py:111`

```text
    def LowCmdHandler(self, msg: LowCmd_):
        if self.mj_data != None:
            for i in range(self.num_motor):
                self.mj_data.ctrl[i] = (
                    msg.motor_cmd[i].tau
                    + msg.motor_cmd[i].kp
                    * (msg.motor_cmd[i].q - self.mj_data.sensordata[i])
                    + msg.motor_cmd[i].kd
                    * (
                        msg.motor_cmd[i].dq
                        - self.mj_data.sensordata[i + self.num_motor]
                    )
                )
```
