import { initializeApp, getApps } from "firebase/app";
import { getFirestore, collection } from "firebase/firestore";

const app =
  getApps()[0] ??
  initializeApp({
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
  });

export const db = getFirestore(app);
export const SHOP_ID = process.env.NEXT_PUBLIC_SHOP_ID ?? "cedar-and-date";
export const shopCol = (name: string) => collection(db, "shops", SHOP_ID, name);
