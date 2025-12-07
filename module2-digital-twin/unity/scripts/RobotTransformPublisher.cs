using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using Unity.Robotics.ROSTCPConnector.MessageTypes.Geometry_msgs;
using Unity.Robotics.ROSTCPConnector.MessageTypes.Std_msgs;
using Unity.Robotics.ROSTCPConnector.ROSGeometry;
using System;

public class RobotTransformPublisher : MonoBehaviour
{
    [Header("Publishing Settings")]
    public string tfTopic = "/tf";
    public string robotBaseFrame = "world";
    public string robotFrame = "unity_robot_base";
    public float publishRate = 30.0f; // Hz

    [Header("Transform Configuration")]
    public Transform robotTransform; // The transform to publish

    private ROSConnection ros;
    private float publishInterval;
    private float lastPublishTime;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        publishInterval = 1.0f / publishRate;
        lastPublishTime = 0;

        if (robotTransform == null)
        {
            robotTransform = this.transform; // Use this object's transform if none specified
        }
    }

    void Update()
    {
        // Check if it's time to publish
        if (Time.time - lastPublishTime >= publishInterval)
        {
            PublishTransform();
            lastPublishTime = Time.time;
        }
    }

    void PublishTransform()
    {
        // Create the transform message
        TransformMsg transformMsg = new TransformMsg();

        // Convert Unity position to ROS coordinates
        // Unity: X-right, Y-up, Z-forward
        // ROS: X-forward, Y-left, Z-up
        Vector3 unityPosition = robotTransform.position;
        transformMsg.translation = new Vector3Msg(
            unityPosition.z,   // ROS X = Unity Z
            -unityPosition.x,  // ROS Y = -Unity X
            unityPosition.y    // ROS Z = Unity Y
        );

        // Convert Unity rotation to ROS coordinates
        Quaternion unityRotation = robotTransform.rotation;
        // Apply coordinate system conversion
        Quaternion rosRotation = new Quaternion(
            -unityRotation.z,  // ROS X = -Unity Z
            -unityRotation.x,  // ROS Y = -Unity X
            unityRotation.y,   // ROS Z = Unity Y
            unityRotation.w    // ROS W = Unity W
        );
        transformMsg.rotation = new QuaternionMsg(
            rosRotation.x,
            rosRotation.y,
            rosRotation.z,
            rosRotation.w
        );

        // Create the TF message
        var tfMsg = new TFMessageMsg();
        var transformStamped = new TransformStampedMsg();

        transformStamped.header = new HeaderMsg();
        transformStamped.header.stamp = new TimeMsg(DateTime.Now);
        transformStamped.header.frame_id = robotBaseFrame;
        transformStamped.child_frame_id = robotFrame;
        transformStamped.transform = transformMsg;

        tfMsg.transforms = new TransformStampedMsg[] { transformStamped };

        // Publish the TF message
        ros.Publish(tfTopic, tfMsg);
    }

    // Helper method to manually publish transform
    public void ForcePublishTransform()
    {
        PublishTransform();
    }
}