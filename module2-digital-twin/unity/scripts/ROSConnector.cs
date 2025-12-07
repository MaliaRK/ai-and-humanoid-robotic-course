using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;

public class ROSConnector : MonoBehaviour
{
    [Header("ROS Connection Settings")]
    public string rosIPAddress = "127.0.0.1";
    public int rosPort = 10000;
    public bool autoConnect = true;

    [Header("Connection Status")]
    public bool isConnected = false;

    private ROSConnection rosConnection;

    void Start()
    {
        if (autoConnect)
        {
            ConnectToROS();
        }
    }

    public void ConnectToROS()
    {
        try
        {
            rosConnection = ROSConnection.GetOrCreateInstance();
            rosConnection.rosIPAddress = rosIPAddress;
            rosConnection.rosPort = rosPort;

            // Test the connection
            isConnected = rosConnection != null;
            Debug.Log($"ROS Connection Status: {(isConnected ? "Connected" : "Disconnected")}");
        }
        catch (System.Exception e)
        {
            Debug.LogError($"Failed to connect to ROS: {e.Message}");
            isConnected = false;
        }
    }

    public void DisconnectFromROS()
    {
        if (rosConnection != null)
        {
            rosConnection = null;
            isConnected = false;
            Debug.Log("Disconnected from ROS");
        }
    }

    // Update is called once per frame
    void Update()
    {
        // Connection status can be checked here if needed
    }
}