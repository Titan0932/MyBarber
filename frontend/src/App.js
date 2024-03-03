import React,{useState, useEffect} from "react";

import 'bootstrap/dist/css/bootstrap.min.css';
import './custom.css'; // Make sure to create this CSS file
// import unknownImg from '../public/img/unknown.png'
import messaging from "./Messaging";
import Paho from "paho-mqtt";

const Table = ({rows}) => {
  const [curUser, setcurUser] = useState({id: 1232, name: "Lucy Ann"})
  const [barbers, setbarbers] = useState([])
  const [bookedBarbers, setbookedBarbers] = useState([])

  useEffect(() => {
    messaging.connectWithPromise().then(response => {
        console.log("Successfully connected to Solace Cloud.", response);
        messaging.subscribe("queueUpdate");
        console.log("USERID: ", curUser.id)
        curUser.id && messaging.subscribe(`enqueueRequest/${curUser.id}`);
        // messaging.subscribe("C138/queueUpdate"); // mock customer ID
    }).catch(error => {
        console.log("Unable to establish connection with Solace Cloud, see above logs for more details.", error);
    });
    messaging.register("queueUpdate",updateBarbers);
    messaging.register("enqueueRequest",displayMsg);
    messaging.register("dequeueUpdate",displayMsg);
  }, []);


  const handleBook = (barberID, action) => {
    let message = new Paho.Message(JSON.stringify(
        {
            "customerID": curUser?.id,
            "barberID": barberID
        }
    ));
    action == "BOOK" ? message.destinationName = "enqueueRequest" : message.destinationName = "dequeueRequest";
    messaging.send(message);
}

  const updateBarbers = (newState) => {
    setbarbers(newState)
  }

  const displayMsg = (msg) => {
    alert(msg)
  }


  return (
    <div className="d-flex justify-content-center">
      <table className="table styled-table">
        <thead>
          <tr>
            <th></th>
            <th>Barber</th>
            <th>Available</th>
            <th>Wait-time</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((item) => (
            <tr key={item.id}>
              <td><img src={'../public/img/unknown.png'} /></td>
              <td>{item.name}</td>
              <td>{item.available? "YES!" : "No :("}</td>
              <td>{item.queue.map((user, index)=> user.id == curUser.id && index * 30)} </td>
              <td><button className="rounded border-1" onClick={() => {handleBook()}}>Book</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};



const App = () => {
  const rows = [
    {
      img: 'img/unknown.jpg',
      id: 1232,
      name: "John Not Doe",
      queue: [{id: 111, name: "Lucy Ann"}, {id: 1232, name: "Lucy Ann"}],
      available: true
    }
  ]
  return (
    <Table rows={rows} />
  );
};

export default App;
