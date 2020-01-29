export interface PersonListModel {
  postid: number;
  name: string;
  branchOfGov: string;
  organizations: any;
  ministry: string;
  position: string;
  gender: string;
  age: string;
  ancestry: string;
  ethnicity: string;
  imageurl: string;
}

export interface PersonDetailModel {
  postid: number;
  userid: number;
  name: string;
  branchOfGov: string;
  organizations: any;
  ministry: string;
  position: string;
  gender: string;
  age: string;
  ancestry: string;
  ethnicity: string;
  imageurl: string;
  updatedtime: string;
  status: string;
  editor: string;
}



export interface UserAvartaColumn {
  id: PersonListModel[];
}
