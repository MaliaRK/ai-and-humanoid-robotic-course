using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using Unity.Robotics.ROSTCPConnector.MessageTypes.Std_msgs;
using Unity.Robotics.ROSTCPConnector.MessageTypes.Geometry_msgs;
using System;

public class HRICommunicationHandler : MonoBehaviour
{
    [Header("HRI Communication Topics")]
    public string hriStatusTopic = "/hri_status";
    public string interactionCommandTopic = "/interaction_commands";
    public string speechTopic = "/tts_input";
    public string gestureTopic = "/robot_gestures";

    [Header("HRI Configuration")]
    public string robotName = "unity_robot";
    public bool enableHRI = true;

    private ROSConnection ros;
    private string lastInteractionStatus = "idle";
    private float statusPublishInterval = 1.0f;
    private float lastStatusPublishTime = 0;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();

        // Subscribe to interaction commands
        ros.Subscribe<StringMsg>(interactionCommandTopic, OnInteractionCommandReceived);

        // Subscribe to speech commands
        ros.Subscribe<StringMsg>(speechTopic, OnSpeechCommandReceived);

        // Subscribe to gesture commands
        ros.Subscribe<StringMsg>(gestureTopic, OnGestureCommandReceived);
    }

    void Update()
    {
        // Periodically publish HRI status
        if (Time.time - lastStatusPublishTime >= statusPublishInterval)
        {
            PublishHRIStatus();
            lastStatusPublishTime = Time.time;
        }
    }

    void OnInteractionCommandReceived(StringMsg command)
    {
        if (!enableHRI) return;

        Debug.Log($"Received interaction command: {command.data}");

        // Process the interaction command
        ProcessInteractionCommand(command.data);
    }

    void OnSpeechCommandReceived(StringMsg speech)
    {
        if (!enableHRI) return;

        Debug.Log($"Received speech command: {speech.data}");

        // Process the speech command
        ProcessSpeechCommand(speech.data);
    }

    void OnGestureCommandReceived(StringMsg gesture)
    {
        if (!enableHRI) return;

        Debug.Log($"Received gesture command: {gesture.data}");

        // Process the gesture command
        ProcessGestureCommand(gesture.data);
    }

    void ProcessInteractionCommand(string command)
    {
        switch (command.ToLower())
        {
            case "wave":
                PerformWaveGesture();
                break;
            case "nod":
                PerformNodGesture();
                break;
            case "shake":
                PerformShakeGesture();
                break;
            case "follow":
                SetInteractionStatus("following");
                break;
            case "stop":
                SetInteractionStatus("stopped");
                break;
            case "reset":
                ResetInteraction();
                break;
            default:
                Debug.Log($"Unknown interaction command: {command}");
                break;
        }
    }

    void ProcessSpeechCommand(string speech)
    {
        // In a real implementation, this might trigger animations or audio
        Debug.Log($"Robot would speak: {speech}");
        SetInteractionStatus($"speaking: {speech}");
    }

    void ProcessGestureCommand(string gesture)
    {
        switch (gesture.ToLower())
        {
            case "point_left":
                PerformPointLeft();
                break;
            case "point_right":
                PerformPointRight();
                break;
            case "point_forward":
                PerformPointForward();
                break;
            case "arm_wave":
                PerformArmWave();
                break;
            default:
                Debug.Log($"Unknown gesture command: {gesture}");
                break;
        }
    }

    void PerformWaveGesture()
    {
        // In a real implementation, this would trigger an animation
        Debug.Log("Performing wave gesture");
        SetInteractionStatus("waving");
    }

    void PerformNodGesture()
    {
        // In a real implementation, this would trigger an animation
        Debug.Log("Performing nod gesture");
        SetInteractionStatus("nodding");
    }

    void PerformShakeGesture()
    {
        // In a real implementation, this would trigger an animation
        Debug.Log("Performing shake gesture");
        SetInteractionStatus("shaking_head");
    }

    void PerformPointLeft()
    {
        Debug.Log("Performing point left gesture");
        SetInteractionStatus("pointing_left");
    }

    void PerformPointRight()
    {
        Debug.Log("Performing point right gesture");
        SetInteractionStatus("pointing_right");
    }

    void PerformPointForward()
    {
        Debug.Log("Performing point forward gesture");
        SetInteractionStatus("pointing_forward");
    }

    void PerformArmWave()
    {
        Debug.Log("Performing arm wave gesture");
        SetInteractionStatus("arm_waving");
    }

    void SetInteractionStatus(string status)
    {
        lastInteractionStatus = status;
        Debug.Log($"Interaction status set to: {status}");
    }

    void ResetInteraction()
    {
        SetInteractionStatus("idle");
        Debug.Log("Interaction reset to idle state");
    }

    void PublishHRIStatus()
    {
        if (!enableHRI) return;

        StringMsg statusMsg = new StringMsg();
        statusMsg.data = $"{{\"robot\":\"{robotName}\",\"status\":\"{lastInteractionStatus}\",\"timestamp\":{DateTime.Now.Ticks}}}";

        ros.Publish(hriStatusTopic, statusMsg);
    }

    // Helper method to send a custom interaction command
    public void SendInteractionCommand(string command)
    {
        StringMsg cmdMsg = new StringMsg();
        cmdMsg.data = command;
        ros.Publish(interactionCommandTopic, cmdMsg);
    }

    // Helper method to send a speech command
    public void SendSpeechCommand(string speech)
    {
        StringMsg speechMsg = new StringMsg();
        speechMsg.data = speech;
        ros.Publish(speechTopic, speechMsg);
    }

    // Helper method to send a gesture command
    public void SendGestureCommand(string gesture)
    {
        StringMsg gestureMsg = new StringMsg();
        gestureMsg.data = gesture;
        ros.Publish(gestureTopic, gestureMsg);
    }

    // Helper method to get current interaction status
    public string GetInteractionStatus()
    {
        return lastInteractionStatus;
    }
}