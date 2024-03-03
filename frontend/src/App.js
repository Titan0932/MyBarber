import React, { useState, useEffect } from 'react';
import './App.css';
import messaging from "./Messaging";
import Paho from "paho-mqtt";

const App = () => {
    const [connected, setConnected] = useState(false);
    const [messages, setMessages] = useState([]);

    const user_id = "C138"; // mock user id

    useEffect(() => {
        messaging.connectWithPromise().then(response => {
            console.log("Successfully connected to Solace Cloud.", response);
            messaging.subscribe(`${user_id}/queueResponse`); 
            messaging.subscribe(`${user_id}/dequeueResponse`);
            setConnected(true);
        }).catch(error => {
            console.log("Unable to establish connection with Solace Cloud, see above logs for more details.", error);
        });
        messaging.register(handleMessage);
    }, []);

    const handleMessage = (message) => {
        setMessages(prevMessages => [...prevMessages, message.payloadString]);
    }

    const handleQueueClick = () => {
        let message = new Paho.Message(JSON.stringify(
            {
                "customerID": "C138",
                "fname": "test_fname",
                "lname": "test_lname",
                "waitTime": 0,
                "barberID": "B124"
            }
        ));
        message.destinationName = "queueRequest";
        messaging.send(message);
    }

    const handleDequeClick = () => {
        let message = new Paho.Message(JSON.stringify(
            {
                "customerID": "C138",
                "fname": "test_fname",
                "lname": "test_lname",
                "waitTime": 0,
                "barberID": "B124"
            }
        ));
        message.destinationName = "dequeueRequest";
        messaging.send(message);
    }

    return (
        <div className="App">
            <div className="buttons">
                {/* <button onClick={handleConnectClick1}>{connected ? 'Disconnect' : 'Connect'}</button>
                <button onClick={handleConnectClick2}>{'Connect2'}</button> */}
                {connected ? <button onClick={handleQueueClick}>Queue</button> : <button disabled>Queue</button>}
                <button onClick={handleDequeClick}>Dequeue</button>
            </div>
            <ol>
                {messages.map((message, index) => {
                    return <li key={index}>{message}</li>
                })}
            </ol>
        </div>
    );
}

export default App;
