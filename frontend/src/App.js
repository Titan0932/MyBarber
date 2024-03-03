import React,{useState, useEffect, useRef} from "react";

import 'bootstrap/dist/css/bootstrap.min.css';
import './custom.css'; // Make sure to create this CSS file
// import unknownImg from '../public/img/unknown.png'
import messaging from "./Messaging";
import data from './data/barbers.json'
import Paho from "paho-mqtt";
import profile from './unknown.png'


const Table = () => {
  const [curUser, setcurUser] = useState({id: "C123", fname: "Jason", lname: "Davies"})
  const [barbers, setbarbers] = useState([])
  const user_id = "C138"; // mock user id
  const [bookedBarb, setBookedBarb] = useState('')
  
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
    if(action == "BOOK") {
      console.log("here!") 
      message.destinationName = "enqueueRequest"
      setBookedBarb(barberID)
    } else{
      console.log("NOWW here!") 
      message.destinationName = "dequeueRequest";
      setBookedBarb('')
    }
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
            <th className="">Barber</th>
            {/* <th>Available</th> */}
            <th className="">Queue Size</th>
            <th className="">Wait-time</th>
            <th className="">Actions</th>
          </tr>
        </thead>
        <tbody>
          {barbers?.map((curBarb) => (
            <tr key={curBarb.id} style={{padding: "1.5rem", "height": "4rem"}} >
              <td className="text-center align-middle" style={{"width": "2rem"}}><img src={profile} style={{width: "2rem"}} /></td>
              <td className="p-2 align-middle">{curBarb.fname + " " + curBarb.lname}</td>
              {/* <td>{curBarb.available? "YES!" : "No :("}</td> */}
              <td className="p-2 align-middle">{curBarb.queue.length}</td>
              <td className="p-2 align-middle">{curBarb.queue.length * 20} </td>
              {console.log(curBarb)}
              {console.log(bookedBarb)}
              <td className="p-2 align-middle" style={{"width": "10rem"}}>
                <button className="rounded border-1" style={{"border": curBarb.id == bookedBarb? "1px solid red": '1px solid green'}} onClick={() => {handleBook(curBarb["id"], (curBarb.id == bookedBarb? "UN-BOOK" : "BOOK"))}}>
                  {curBarb.id == bookedBarb? "UN-BOOK" : "BOOK"}
                </button>
              </td>
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
