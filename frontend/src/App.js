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
        let message = new Paho.Message(JSON.stringify({text: "Hello"}));
        message.destinationName = "hello";
        messaging.send(message);
    }

    const handleConnectClick = () => {
        if (connected) {
            messaging.disconnect();
            setConnected(false);
        } else {
            messaging.connectWithPromise().then(response => {
                console.log("Successfully connected to Solace Cloud.", response);
                messaging.subscribe("hello");
                setConnected(true);
            }).catch(error => {
                console.log("Unable to establish connection with Solace Cloud, see above logs for more details.", error);
            });
        }
    }

    return (
        <div className="App">
            <div className="buttons">
                <button onClick={handleConnectClick}>{connected ? 'Disconnect' : 'Connect'}</button>
                {connected ? <button onClick={handleSendClick}>Send</button> : <button disabled>Send</button>}
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
