using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using Unity.Robotics.ROSTCPConnector.MessageTypes.Sensor_msgs;
using Unity.Robotics.ROSTCPConnector.MessageTypes.Geometry_msgs;
using Unity.Robotics.ROSTCPConnector.MessageTypes.Std_msgs;
using System;

public class SensorDataPublisher : MonoBehaviour
{
    [Header("Sensor Configuration")]
    public string sensorType = "camera"; // Options: "camera", "lidar", "imu", "depth"
    public string sensorTopic = "/unity_sensor_data";
    public float publishRate = 10.0f; // Hz

    [Header("Camera Configuration")]
    public Camera sensorCamera;
    public int imageWidth = 640;
    public int imageHeight = 480;

    [Header("IMU Configuration")]
    public bool useIMU = false;
    public Vector3 imuOffset = Vector3.zero;

    private ROSConnection ros;
    private float publishInterval;
    private float lastPublishTime;
    private RenderTexture renderTexture;
    private Texture2D tempTexture;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        publishInterval = 1.0f / publishRate;
        lastPublishTime = 0;

        if (sensorCamera == null)
        {
            sensorCamera = GetComponent<Camera>();
        }

        if (sensorCamera != null && sensorType == "camera")
        {
            SetupCameraSensor();
        }
    }

    void Update()
    {
        // Check if it's time to publish
        if (Time.time - lastPublishTime >= publishInterval)
        {
            PublishSensorData();
            lastPublishTime = Time.time;
        }
    }

    void SetupCameraSensor()
    {
        // Create render texture for camera capture
        renderTexture = new RenderTexture(imageWidth, imageHeight, 24);
        sensorCamera.targetTexture = renderTexture;

        tempTexture = new Texture2D(imageWidth, imageHeight, TextureFormat.RGB24, false);
    }

    void PublishSensorData()
    {
        switch (sensorType)
        {
            case "camera":
                PublishCameraData();
                break;
            case "imu":
                PublishIMUData();
                break;
            case "lidar":
                PublishLidarData();
                break;
            case "depth":
                PublishDepthData();
                break;
        }
    }

    void PublishCameraData()
    {
        if (sensorCamera == null) return;

        // Capture the image from the camera
        RenderTexture.active = renderTexture;
        tempTexture.ReadPixels(new Rect(0, 0, imageWidth, imageHeight), 0, 0);
        tempTexture.Apply();

        // Convert texture to bytes
        byte[] imageBytes = tempTexture.EncodeToJPG(85); // 85% quality

        // Create ROS Image message
        ImageMsg imageMsg = new ImageMsg();
        imageMsg.header = new HeaderMsg();
        imageMsg.header.stamp = new TimeMsg(DateTime.Now);
        imageMsg.header.frame_id = sensorCamera.name + "_frame";
        imageMsg.height = (uint)imageHeight;
        imageMsg.width = (uint)imageWidth;
        imageMsg.encoding = "rgb8";
        imageMsg.is_bigendian = 0;
        imageMsg.step = (uint)(imageWidth * 3); // 3 bytes per pixel (RGB)
        imageMsg.data = imageBytes;

        // Publish the image
        ros.Publish(sensorTopic, imageMsg);
    }

    void PublishIMUData()
    {
        // Create ROS IMU message
        ImuMsg imuMsg = new ImuMsg();
        imuMsg.header = new HeaderMsg();
        imuMsg.header.stamp = new TimeMsg(DateTime.Now);
        imuMsg.header.frame_id = transform.name + "_imu_frame";

        // Set orientation (from transform rotation)
        Quaternion unityRotation = transform.rotation;
        // Convert Unity rotation to ROS coordinates
        Quaternion rosRotation = new Quaternion(
            -unityRotation.z,  // ROS X = -Unity Z
            -unityRotation.x,  // ROS Y = -Unity X
            unityRotation.y,   // ROS Z = Unity Y
            unityRotation.w    // ROS W = Unity W
        );
        imuMsg.orientation = new QuaternionMsg(
            rosRotation.x,
            rosRotation.y,
            rosRotation.z,
            rosRotation.w
        );

        // Set angular velocity (simplified - would come from rigidbody in real implementation)
        imuMsg.angular_velocity = new Vector3Msg(0, 0, 0);

        // Set linear acceleration (simplified - would come from physics in real implementation)
        imuMsg.linear_acceleration = new Vector3Msg(0, 0, 9.81f); // Gravity

        // Publish the IMU data
        ros.Publish(sensorTopic, imuMsg);
    }

    void PublishLidarData()
    {
        // Create ROS LaserScan message
        LaserScanMsg laserScanMsg = new LaserScanMsg();
        laserScanMsg.header = new HeaderMsg();
        laserScanMsg.header.stamp = new TimeMsg(DateTime.Now);
        laserScanMsg.header.frame_id = transform.name + "_lidar_frame";

        // Set laser scan parameters (simplified)
        laserScanMsg.angle_min = -Mathf.PI / 2; // -90 degrees
        laserScanMsg.angle_max = Mathf.PI / 2;  // 90 degrees
        laserScanMsg.angle_increment = Mathf.PI / 180; // 1 degree increment
        laserScanMsg.time_increment = 0.0f;
        laserScanMsg.scan_time = 1.0f / publishRate;
        laserScanMsg.range_min = 0.1f;
        laserScanMsg.range_max = 10.0f;

        // Calculate number of points
        int numPoints = Mathf.CeilToInt((laserScanMsg.angle_max - laserScanMsg.angle_min) / laserScanMsg.angle_increment) + 1;
        laserScanMsg.ranges = new float[numPoints];

        // Fill with dummy data (in real implementation, this would come from raycasting)
        for (int i = 0; i < numPoints; i++)
        {
            laserScanMsg.ranges[i] = 5.0f; // Default range
        }

        // Publish the laser scan
        ros.Publish(sensorTopic, laserScanMsg);
    }

    void PublishDepthData()
    {
        // For depth data, we could publish a PointCloud2 message or a depth image
        // This is a simplified implementation that publishes dummy depth data
        PointCloud2Msg pointCloudMsg = new PointCloud2Msg();
        pointCloudMsg.header = new HeaderMsg();
        pointCloudMsg.header.stamp = new TimeMsg(DateTime.Now);
        pointCloudMsg.header.frame_id = transform.name + "_depth_frame";

        // Set up point cloud fields (x, y, z, intensity)
        pointCloudMsg.fields = new PointFieldMsg[4];
        pointCloudMsg.fields[0] = new PointFieldMsg("x", 0, PointFieldMsg.FLOAT32, 1);
        pointCloudMsg.fields[1] = new PointFieldMsg("y", 4, PointFieldMsg.FLOAT32, 1);
        pointCloudMsg.fields[2] = new PointFieldMsg("z", 8, PointFieldMsg.FLOAT32, 1);
        pointCloudMsg.fields[3] = new PointFieldMsg("intensity", 12, PointFieldMsg.FLOAT32, 1);

        pointCloudMsg.is_bigendian = false;
        pointCloudMsg.point_step = 16; // 4 fields * 4 bytes each
        pointCloudMsg.row_step = pointCloudMsg.point_step * 100; // 100 points
        pointCloudMsg.height = 1;
        pointCloudMsg.width = 100;
        pointCloudMsg.is_dense = true;

        // Create dummy point cloud data
        int pointCount = 100;
        byte[] data = new byte[pointCount * pointCloudMsg.point_step];
        pointCloudMsg.data = data;

        // Publish the point cloud
        ros.Publish(sensorTopic, pointCloudMsg);
    }

    // Helper method to manually publish sensor data
    public void ForcePublishSensorData()
    {
        PublishSensorData();
    }

    void OnDestroy()
    {
        if (renderTexture != null)
        {
            renderTexture.Release();
        }
        if (tempTexture != null)
        {
            Destroy(tempTexture);
        }
    }
}