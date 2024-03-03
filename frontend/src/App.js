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
            messaging.subscribe(`enqueueResponse/${user_id}`); 
            messaging.subscribe(`dequeueResponse/${user_id}`);
            setConnected(true);
        }).catch(error => {
            console.log("Unable to establish connection with Solace Cloud, see above logs for more details.", error);
        });
        messaging.register(handleMessage);
    }, []);

    const handleMessage = (message) => {
        setMessages(prevMessages => [...prevMessages, message.payloadString]);
    }

    const handleEnqueueClick = () => {
        let message = new Paho.Message(JSON.stringify(
            {
                "customerID": "C138",
                "fname": "test_fname",
                "lname": "test_lname",
                "waitTime": 0,
                "barberID": "B124"
            }
        ));
        message.destinationName = "enqueueRequest";
        messaging.send(message);
    }

    const handleDequeueClick = () => {
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
                {connected ? <button onClick={handleEnqueueClick}>Enqueue</button> : <button disabled>Queue</button>}
                <button onClick={handleDequeueClick}>Dequeue</button>
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
