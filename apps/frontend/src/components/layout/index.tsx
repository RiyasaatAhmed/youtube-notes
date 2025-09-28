import { Fragment } from "react/jsx-runtime";
import { Outlet } from "react-router-dom";
import { Header } from "./header";
import { Page } from "./page";

export function Layout() {
  return (
    <Fragment>
      <Header />
      <Page>
        <Outlet />
      </Page>
    </Fragment>
  );
}
