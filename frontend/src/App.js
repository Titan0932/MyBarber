import React,{useState, useEffect, useRef} from "react";

import 'bootstrap/dist/css/bootstrap.min.css';
import './custom.css'; // Make sure to create this CSS file
// import unknownImg from '../public/img/unknown.png'
import messaging from "./Messaging";
import data from './data/barbers.json'
import Paho from "paho-mqtt";




const Table = () => {
  const curUser = useRef({id: "C123", fname: "Jason", lname: "Davies"})
  const [barbers, setbarbers] = useState([])
  const user_id = "C138"; // mock user id

  
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
    setbarbers(data);
console.log(data)
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
    console.log(newState)
    setbarbers(newState)
  }

  const displayMsg = (msg) => {
    alert(msg)
  }


  return (
    <div className="d-flex justify-content-center">
      <table className="table styled-table barbers">
        <thead>
          <tr>
            <th></th>
            <th className="text-center">Barber</th>
            {/* <th>Available</th> */}
            <th className="text-center">Queue Size</th>
            <th className="text-center">Wait-time</th>
            <th className="text-center">Actions</th>
          </tr>
        </thead>
        <tbody>
          {barbers?.map((curBarb) => (
            <tr key={curBarb.id}>
              <td className="text-center"><img src={'../public/img/unknown.png'} /></td>
              <td className="text-center">{curBarb.fname + " " + curBarb.lname}</td>
              {/* <td>{curBarb.available? "YES!" : "No :("}</td> */}
              <td className="text-center">{curBarb.queue.length}</td>
              <td className="text-center">{curBarb.queue.length * 30} </td>
              <td className="text-center"><button className="rounded border-1" onClick={() => {handleBook(curBarb["id"], (curBarb.queue.map((user)=> user.id == curUser.id) == false? "BOOKED!": "BOOK" ))}}>Book</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};



const App = () => {
  
  return (
    <Table/>
  );
};

export default App;
