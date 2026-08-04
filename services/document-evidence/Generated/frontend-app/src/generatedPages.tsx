import type { ReactNode } from "react";
import { DocumentfragmentsPage } from "./generated-ts/documentfragments/pages/DocumentfragmentsPage.generated";
import { DocumentrevisionsPage } from "./generated-ts/documentrevisions/pages/DocumentrevisionsPage.generated";
import { DocumentsPage } from "./generated-ts/documents/pages/DocumentsPage.generated";
import { PermissionsPage } from "./generated-ts/permissions/pages/PermissionsPage.generated";
import { ProcessingjobsPage } from "./generated-ts/processingjobs/pages/ProcessingjobsPage.generated";
import { RolepermissionsPage } from "./generated-ts/rolepermissions/pages/RolepermissionsPage.generated";
import { RolesPage } from "./generated-ts/roles/pages/RolesPage.generated";
import { StaffpositionassignmentsPage } from "./generated-ts/staffpositionassignments/pages/StaffpositionassignmentsPage.generated";
import { StaffpositionrolesPage } from "./generated-ts/staffpositionroles/pages/StaffpositionrolesPage.generated";
import { StaffpositionsPage } from "./generated-ts/staffpositions/pages/StaffpositionsPage.generated";
import { StoredobjectsPage } from "./generated-ts/storedobjects/pages/StoredobjectsPage.generated";

export interface GeneratedPage {
  route: string;
  title: string;
  element: ReactNode;
}

export const generatedPages: GeneratedPage[] = [
  { route: "/documentfragments", title: "Documentfragments", element: <DocumentfragmentsPage /> },
  { route: "/documentrevisions", title: "Documentrevisions", element: <DocumentrevisionsPage /> },
  { route: "/documents", title: "Documents", element: <DocumentsPage /> },
  { route: "/permissions", title: "Permissions", element: <PermissionsPage /> },
  { route: "/processingjobs", title: "Processingjobs", element: <ProcessingjobsPage /> },
  { route: "/rolepermissions", title: "Rolepermissions", element: <RolepermissionsPage /> },
  { route: "/roles", title: "Roles", element: <RolesPage /> },
  { route: "/staffpositionassignments", title: "Staffpositionassignments", element: <StaffpositionassignmentsPage /> },
  { route: "/staffpositionroles", title: "Staffpositionroles", element: <StaffpositionrolesPage /> },
  { route: "/staffpositions", title: "Staffpositions", element: <StaffpositionsPage /> },
  { route: "/storedobjects", title: "Storedobjects", element: <StoredobjectsPage /> },
];
