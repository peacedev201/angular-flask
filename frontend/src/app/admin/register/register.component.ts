import { Component, OnInit } from '@angular/core';
import { FormGroup, Validators, FormBuilder } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from 'src/app/services/auth.service';
import { AlertService } from 'src/app/services/alert.service';
import { first } from 'rxjs/operators';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-register ',
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss']
})
export class RegisterComponent implements OnInit {

  registerForm: FormGroup = this.formBuilder.group({
    email: ['user@gmail.com', [Validators.required, Validators.email]],
    username: ['user', Validators.required],
    password: ['password', [Validators.required, Validators.minLength(6)]],
    rpassword: ['password', [Validators.required, Validators.minLength(6)]]
  });
  loading = false;
  submitted = false;
  returnUrl: string;
  error = null;
  constructor(
    private formBuilder: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private authenticationService: AuthService,
    public alertService: AlertService,
    private toastr: ToastrService
  ) {
    // redirect to home if already logged in
    if (this.authenticationService.currentUserValue) {
      this.router.navigate(['/admin']);
    }
  }

  ngOnInit() {


    // get return url from route parameters or default to '/'
    this.returnUrl = this.route.snapshot.queryParams.returnUrl || '/admin';
  }

  onSubmit() {
    this.submitted = true;

    // reset alerts on submit
    this.alertService.clear();

    // stop here if form is invalid
    if (this.registerForm.invalid) {
      return;
    }

    if (this.registerForm.controls.password.value !== this.registerForm.controls.rpassword.value) {
      return;
    }

    this.loading = true;
    this.error = '';
    this.authenticationService.registerUser(this.registerForm.controls.email.value, this.registerForm.controls.username.value,
      this.registerForm.controls.password.value)
      .subscribe(
        data => {
          if (data.message === 'Success') {
            // console.log("this is test")
            this.router.navigate([`/login`]);
            this.toastr.success('Please wait for admin to approve your request!', 'Success!',{timeOut: 10000});
          } else {
            this.alertService.error(data.message);
            this.error = data.message;
            // this.alertService.getAlert().subscribe((res) => {
            //   console.log(res);
            // });
          }
        },
        error => {
          this.alertService.error(error);
          this.error = error;
          this.loading = false;
        });
  }
}
