import options from "./messaging-options";
import Paho from "paho-mqtt";

class Messaging extends Paho.Client {

	constructor() {
		super(options.invocationContext.host, Number(options.invocationContext.port), options.invocationContext.clientId);
		this.onMessageArrived = this.handleMessage.bind(this);
		this.callbacks = {};
	}

	connectWithPromise() {
		return new Promise((resolve, reject) => {
			options.onSuccess = resolve;
			options.onFailure = reject;
			this.connect(options);
		});
	}

	// called when the client loses its connection
	onConnectionLost(responseObject) {
		if (responseObject.errorCode !== 0) {
			console.log("Connection lost with Solace Cloud");
		}
		// Add auto connect logic with backoff here if you want to automatically reconnect
	}

	register(topic, callback) {
		this.callbacks[topic]= callback;
	}
	
	// called when a message arrives
	handleMessage(message) {
    console.log("Received message", message.payloadString);
    const topic = message.destinationName;
		let respObj = JSON.parse(message.payloadString)
    if (topic === "queueUpdate") {
			console.log("AYYO")
      this.callbacks["queueUpdate"](respObj);
    } else if(topic === `enqueueResponse/${respObj.id}`){
			console.log("enqueueResponse--->")
      this.callbacks[topic](respObj.message);
		}else if(topic === `dequeueResponse/${respObj.id}`){
      this.callbacks[topic](respObj.message);
		}else{
      console.log(`No handler for topic ${topic}`);
    }
  }
}

const messaging = new Messaging();
export default messaging;