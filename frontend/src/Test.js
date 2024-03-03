import React, { useState, useEffect } from 'react';
import './App.css';
import messaging from "./Messaging";
import Paho from "paho-mqtt";

const App = () => {
    const [connected, setConnected] = useState(false);
    const [messages, setMessages] = useState([]);

    useEffect(() => {
        messaging.register(handleMessage);
    }, []);

    const handleMessage = (message) => {
        setMessages(prevMessages => [...prevMessages, message.payloadString]);
    }

    const handleSendClick = () => {
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

    const handleSendClick2 = () => {
        let message = new Paho.Message(JSON.stringify({text: "notificationasdasd"}));
        message.destinationName = "notification";
        messaging.send(message);
    }

    const handleConnectClick1 = () => {
        if (connected) {
            messaging.disconnect();
            setConnected(false);
        } else {
            messaging.connectWithPromise().then(response => {
                console.log("Successfully connected to Solace Cloud.", response);
                messaging.subscribe("notification");
                messaging.subscribe("C138/queueUpdate"); // mock customer ID
                setConnected(true);
            }).catch(error => {
                console.log("Unable to establish connection with Solace Cloud, see above logs for more details.", error);
            });
        }
    }
    const handleConnectClick2 = () => {
       
            messaging.connectWithPromise().then(response => {
                console.log("Successfully connected to Solace Cloud.", response);
                messaging.subscribe("queue");
            }).catch(error => {
                console.log("Unable to establish connection with Solace Cloud, see above logs for more details.", error);
            });
    }

    return (
        <div className="App">
            <div className="buttons">
                <button onClick={handleConnectClick1}>{connected ? 'Disconnect' : 'Connect'}</button>
                <button onClick={handleConnectClick2}>{'Connect2'}</button>
                {connected ? <button onClick={handleSendClick}>Send</button> : <button disabled>Send</button>}
                <button onClick={handleSendClick2}>Send2</button>
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
