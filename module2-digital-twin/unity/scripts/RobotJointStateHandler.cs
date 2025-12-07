using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using Unity.Robotics.ROSTCPConnector.MessageTypes.Sensor_msgs;
using System.Linq;

public class RobotJointStateHandler : MonoBehaviour
{
    [Header("Robot Configuration")]
    public string robotName = "humanoid_robot";
    public string jointStatesTopic = "/joint_states";

    [Header("Joint Mapping")]
    public JointMapping[] jointMappings;

    [System.Serializable]
    public class JointMapping
    {
        public string jointName; // Name from ROS joint states
        public Transform jointTransform; // Corresponding transform in Unity
        public float positionMultiplier = 1.0f; // Multiplier for position conversion
        public float offset = 0.0f; // Offset to apply to position
    }

    private ROSConnection ros;
    private Dictionary<string, int> jointNameToIndex = new Dictionary<string, int>();
    private float[] lastJointPositions;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();

        // Register the callback for receiving joint state messages
        ros.Subscribe<JointStateMsg>(jointStatesTopic, OnJointStateReceived);

        // Initialize joint name to index mapping
        for (int i = 0; i < jointMappings.Length; i++)
        {
            if (!jointNameToIndex.ContainsKey(jointMappings[i].jointName))
            {
                jointNameToIndex[jointMappings[i].jointName] = i;
            }
        }

        lastJointPositions = new float[jointMappings.Length];
    }

    void OnJointStateReceived(JointStateMsg jointState)
    {
        // Update joint positions based on received joint state
        for (int i = 0; i < jointState.name.Length; i++)
        {
            string jointName = jointState.name[i];

            if (jointNameToIndex.ContainsKey(jointName))
            {
                int jointIndex = jointNameToIndex[jointName];

                if (jointIndex < jointMappings.Length && jointMappings[jointIndex].jointTransform != null)
                {
                    // Get the position for this joint
                    float position = 0f;
                    if (i < jointState.position.Length)
                    {
                        position = (float)jointState.position[i];
                        lastJointPositions[jointIndex] = position;
                    }
                    else if (i < jointState.velocity.Length)
                    {
                        // If position is not available, try to integrate velocity
                        position = lastJointPositions[jointIndex] + (float)jointState.velocity[i] * Time.deltaTime;
                        lastJointPositions[jointIndex] = position;
                    }

                    // Apply the position to the Unity transform
                    ApplyJointPosition(jointMappings[jointIndex], position);
                }
            }
        }
    }

    void ApplyJointPosition(JointMapping jointMapping, float position)
    {
        // Apply position multiplier and offset
        float adjustedPosition = position * jointMapping.positionMultiplier + jointMapping.offset;

        // Apply rotation to the joint transform
        // This assumes the joint rotates around the Z-axis; adjust as needed
        jointMapping.jointTransform.localRotation = Quaternion.Euler(
            jointMapping.jointTransform.localRotation.eulerAngles.x,
            jointMapping.jointTransform.localRotation.eulerAngles.y,
            adjustedPosition * Mathf.Rad2Deg // Convert radians to degrees
        );
    }

    // Helper method to manually set joint positions (useful for testing)
    public void SetJointPosition(string jointName, float position)
    {
        if (jointNameToIndex.ContainsKey(jointName))
        {
            int jointIndex = jointNameToIndex[jointName];
            if (jointIndex < jointMappings.Length && jointMappings[jointIndex].jointTransform != null)
            {
                ApplyJointPosition(jointMappings[jointIndex], position);
            }
        }
    }
}