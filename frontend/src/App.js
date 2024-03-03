import React,{useState, useEffect, useRef} from "react";
import random from 'random'

import 'bootstrap/dist/css/bootstrap.min.css';
import './custom.css'; // Make sure to create this CSS file
// import unknownImg from '../public/img/unknown.png'
import messaging from "./Messaging";
import data from './data/barbers.json'
import Paho from "paho-mqtt";
import profile from './unknown.png'

const UserProfile = ({ user }) => {
  return (
    <div className="user-profile">
      <img src={profile} alt="User Profile" style={{ width: "50px", height: "50px", borderRadius: "25px"}} />
      <div>{`${user.fname} ${user.lname}`}</div>
      <div>{`ID: ${user.id}`}</div>
      <br></br>
    </div>
  );
};

const Table = ({ curUser }) => {
  // const [curUser, setcurUser] = useState({id: "C149", fname: "Scarlett", lname: "Reyes"})
  const [barbers, setbarbers] = useState([])
  const [bookedBarb, setBookedBarb] = useState('')
  
  useEffect(() => {
    messaging.connectWithPromise().then(response => {
        console.log("Successfully connected to Solace Cloud.", response);
        messaging.subscribe("queueUpdate");
        console.log("USERID: ", curUser.id)
        curUser.id && messaging.subscribe(`enqueueResponse/${curUser.id}`);
        curUser.id && messaging.subscribe(`dequeueResponse/${curUser.id}`);
    }).catch(error => {
        console.log("Unable to establish connection with Solace Cloud, see above logs for more details.", error);
    });
    messaging.register("queueUpdate",updateBarbers);
    messaging.register(`enqueueResponse/${curUser.id}`,displayMsg);
    messaging.register(`dequeueResponse/${curUser.id}`,displayMsg);
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
      console.log("BarberNew: ", barberID)
      console.log("booked: ", bookedBarb)
      message.destinationName = `enqueueRequest`
      setBookedBarb(barberID)
    } else{
      console.log("NOWW here!") 
      message.destinationName = `dequeueRequest`;
      setBookedBarb('')
    }
    messaging.send(message);
}

  const updateBarbers = (newState) => {
    console.log(newState)
    setbarbers(newState)
  }

  const displayMsg = (msg) => {
    console.log(msg)
    alert(msg)
  }

  const updateWaitTime = (barber, curUser) => {
    for (let i = 0; i < barber.queue.length; i++) {
      if (barber.queue[i].id == curUser.id) {
        return (i+1)*20
      }
    }
    return barber.queue.length*20
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
            <th className="">Queue Position</th>
            <th className="">Wait-time</th>
            <th className="">Actions</th>
          </tr>
        </thead>
        <tbody>
          {barbers?.map((curBarb) => (
            console.log(curBarb),
            <tr key={curBarb.id} style={{padding: "1.5rem", "height": "4rem"}} >
              <td className="text-center align-middle" style={{"width": "2rem"}}><img src={profile} style={{width: "2rem"}} /></td>
              <td className="p-2 align-middle">{curBarb.fname + " " + curBarb.lname}</td>
              {/* <td>{curBarb.available? "YES!" : "No :("}</td> */}
              <td className="p-2 align-middle">{curBarb.queue.length}</td>
              <td className="p-2 align-middle">{curBarb.id != bookedBarb? "--": curBarb.queue.map((cust, index) => (cust.id == curUser.id && index+1))}</td>
              <td className="p-2 align-middle">{updateWaitTime(curBarb, curUser)} </td>
              <td className="p-2 align-middle" style={{"width": "10rem"}}>
                <button className="rounded border-1" 
                    style={{"border": curBarb.id == bookedBarb? "1px solid red": '1px solid green'}} 
                      onClick={() => {handleBook(curBarb["id"], (curBarb.id == bookedBarb? "UN-BOOK" : "BOOK"))}}
                        disabled={bookedBarb.length>0 && curBarb.id != bookedBarb}>
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
  let curUser;
  if (random.randomInt(0, 1000) < 500) {
    curUser = { id: "C149", fname: "Scarlett", lname: "Reyes" };
  } else {
    curUser = { id: "C148", fname: "Jackson", lname: "Jimenez" };
  }

  return (
    <div>
      <UserProfile user={curUser} />
      <Table curUser={curUser} />
    </div>
   
  );
};

export default App;
